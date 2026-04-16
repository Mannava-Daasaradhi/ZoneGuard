"""
Feature 12 — SmartClaim Autopilot: LLM Client.

Wraps the Anthropic Claude API (claude-sonnet-4-6) and enforces
structured JSON output for autopilot decisions.

Environment variables (all FEATURE12_ prefixed):
  FEATURE12_LLM_MODEL          default: claude-sonnet-4-6
  FEATURE12_LLM_MAX_TOKENS     default: 1024
  ANTHROPIC_API_KEY            shared with rest of ZoneGuard
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import anthropic

from backend.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------

@dataclass
class LLMDecisionInput:
    """All context sent to the LLM for a single claim decision."""
    claim_id: str
    zone_id: str
    policy_id: str
    claimed_amount: float
    calculated_payout: float         # formula-derived; LLM cannot override this
    fraud_score: float
    fraud_risk_level: str
    fraud_flags: list[str]
    signal_summary: dict             # from Step 1
    onchain_validation: dict         # from Step 3
    policy_coverage_amount: float
    policy_deductible: float
    claim_description: str = ""

    def to_prompt_context(self) -> str:
        """Serialise to human-readable block for the prompt."""
        return json.dumps(
            {
                "claim_id": self.claim_id,
                "zone_id": self.zone_id,
                "policy_id": self.policy_id,
                "claimed_amount": self.claimed_amount,
                "formula_calculated_payout": self.calculated_payout,
                "policy_coverage_amount": self.policy_coverage_amount,
                "policy_deductible": self.policy_deductible,
                "fraud_analysis": {
                    "score": self.fraud_score,
                    "risk_level": self.fraud_risk_level,
                    "flags": self.fraud_flags,
                },
                "quad_signal_summary": self.signal_summary,
                "onchain_validation": self.onchain_validation,
                "claim_description": self.claim_description,
            },
            indent=2,
        )


@dataclass
class LLMDecisionOutput:
    """Validated, parsed response from the LLM."""
    decision: str            # APPROVE | REJECT | ESCALATE
    confidence: float        # 0.0 – 1.0
    reasoning: str
    payout_amount: float     # LLM-proposed; may be overridden by guard rails
    raw_response: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "payout_amount": self.payout_amount,
            "raw_response": self.raw_response,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
        }


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the SmartClaim Autopilot decision engine for ZoneGuard, \
a decentralised parametric insurance protocol.

Your role is to evaluate insurance claims and produce a structured JSON decision.

## Decision criteria
- APPROVE   : Fraud score < 0.55 AND signals validate the event AND formula payout ≤ coverage
- REJECT    : Fraud score ≥ 0.55 OR critical signals missing OR on-chain validation failed
- ESCALATE  : Ambiguous evidence, borderline fraud score (0.40–0.54), or insufficient signals

## Output format — respond ONLY with valid JSON, no markdown fences, no preamble:
{
  "decision": "APPROVE" | "REJECT" | "ESCALATE",
  "confidence": <float 0.0–1.0>,
  "reasoning": "<concise explanation, max 3 sentences>",
  "payout_amount": <float — must equal formula_calculated_payout from the input; you cannot change it>
}

## Hard constraints
- payout_amount MUST exactly equal the formula_calculated_payout provided in the input.
- confidence must be a decimal between 0.0 and 1.0 (e.g. 0.92 not 92).
- Your reasoning must reference specific signals or fraud flags.
- Never fabricate data not present in the input context.
"""

USER_PROMPT_TEMPLATE = """Evaluate the following insurance claim and return your JSON decision.

## Claim Context
{context}

Respond with only the JSON object as specified.
"""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class AutopilotLLMClient:
    """
    Thin, stateless wrapper around the Anthropic Messages API.
    One instance per application; safe to share across async tasks.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self._model = model or settings.FEATURE12_LLM_MODEL
        self._max_tokens = max_tokens or settings.FEATURE12_LLM_MAX_TOKENS
        self._client = anthropic.Anthropic(
            api_key=api_key or settings.ANTHROPIC_API_KEY
        )
        logger.info(
            "AutopilotLLMClient initialised",
            extra={"model": self._model, "max_tokens": self._max_tokens},
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def decide(self, decision_input: LLMDecisionInput) -> LLMDecisionOutput:
        """
        Call the LLM and parse the structured decision.

        Raises
        ------
        LLMParseError
            If the model returns malformed JSON after retries.
        anthropic.APIError
            Propagated from the Anthropic client on network/auth failures.
        """
        user_content = USER_PROMPT_TEMPLATE.format(
            context=decision_input.to_prompt_context()
        )

        t0 = time.perf_counter()
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        latency_ms = (time.perf_counter() - t0) * 1000

        raw_text = self._extract_text(response)
        logger.debug(
            "LLM raw response",
            extra={"claim_id": decision_input.claim_id, "raw": raw_text[:500]},
        )

        parsed = self._parse_decision(raw_text, decision_input)
        parsed.raw_response = raw_text
        parsed.model = self._model
        parsed.input_tokens = response.usage.input_tokens
        parsed.output_tokens = response.usage.output_tokens
        parsed.latency_ms = round(latency_ms, 2)

        logger.info(
            "LLM decision produced",
            extra={
                "claim_id": decision_input.claim_id,
                "decision": parsed.decision,
                "confidence": parsed.confidence,
                "latency_ms": parsed.latency_ms,
            },
        )
        return parsed

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(response) -> str:
        """Pull plain text from the Messages API response."""
        for block in response.content:
            if block.type == "text":
                return block.text.strip()
        return ""

    def _parse_decision(
        self, raw: str, decision_input: LLMDecisionInput
    ) -> LLMDecisionOutput:
        """
        Parse and validate the LLM JSON output.
        Strips markdown fences if present; raises LLMParseError on failure.
        """
        # Strip optional ```json ... ``` fences
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMParseError(
                f"LLM returned non-JSON for claim {decision_input.claim_id}: {exc}"
            ) from exc

        # Validate required fields
        required = {"decision", "confidence", "reasoning", "payout_amount"}
        missing = required - data.keys()
        if missing:
            raise LLMParseError(
                f"LLM response missing fields {missing} for claim {decision_input.claim_id}"
            )

        decision = str(data["decision"]).upper()
        if decision not in ("APPROVE", "REJECT", "ESCALATE"):
            raise LLMParseError(
                f"Invalid decision value '{decision}' for claim {decision_input.claim_id}"
            )

        try:
            confidence = float(data["confidence"])
        except (TypeError, ValueError) as exc:
            raise LLMParseError(f"Invalid confidence value: {exc}") from exc

        if not (0.0 <= confidence <= 1.0):
            raise LLMParseError(
                f"Confidence {confidence} out of range [0, 1] for claim {decision_input.claim_id}"
            )

        try:
            payout_amount = float(data["payout_amount"])
        except (TypeError, ValueError) as exc:
            raise LLMParseError(f"Invalid payout_amount: {exc}") from exc

        return LLMDecisionOutput(
            decision=decision,
            confidence=confidence,
            reasoning=str(data.get("reasoning", "")),
            payout_amount=payout_amount,
        )


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LLMParseError(ValueError):
    """Raised when the LLM response cannot be parsed into a valid decision."""
