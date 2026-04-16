# Feature 12 — SmartClaim Autopilot: Change Log

## Summary

Feature 12 introduces the **SmartClaim Autopilot**, an LLM-driven parametric
claim processing pipeline.  It is fully isolated in `backend/features/feature_12/`
and touches no existing files.

---

## Files Created

| Path | Purpose |
|---|---|
| `backend/features/feature_12/__init__.py` | Package marker |
| `backend/features/feature_12/models.py` | ORM tables (f12_ prefix) |
| `backend/features/feature_12/llm_client.py` | Claude API wrapper |
| `backend/features/feature_12/guard_rails.py` | Five guard-rail implementations |
| `backend/features/feature_12/autopilot_service.py` | 5-step pipeline service |
| `backend/features/feature_12/autopilot_router.py` | FastAPI router |
| `.env.feature-12.example` | Environment variable template |
| `backend/features/feature_12/CHANGES.md` | This file |

## Files NOT Modified

Per spec, the following files were **not modified**:

| File | Reason |
|---|---|
| `backend/models/zones.py` | Core domain models — Feature 12 creates its own `models.py` |
| `backend/ml/fraud_shield.py` | Imported read-only; `FraudShield` class is instantiated in `autopilot_service.py` |
| `backend/api/router.py` | See integration instructions below |

---

## Database Migration

Feature 12 introduces three new tables.  Run Alembic (or equivalent) after
adding the `Feature12Base` metadata to your migration target:

```python
# In your Alembic env.py, add:
from backend.features.feature_12.models import Feature12Base
target_metadata = [Base.metadata, Feature12Base.metadata]
```

New tables:

| Table | Description |
|---|---|
| `f12_autopilot_runs` | One row per pipeline execution |
| `f12_autopilot_overrides` | Human override records (Guard Rail 4) |
| `f12_drift_snapshots` | Statistical drift monitor snapshots (Guard Rail 5) |

---

## Router Integration

**DO NOT modify `backend/api/router.py` directly.**

Add the following two lines to the application factory (e.g. `backend/main.py`
or wherever `app.include_router(...)` calls are made):

```python
from backend.features.feature_12.autopilot_router import router as f12_router

app.include_router(f12_router, prefix="/api/v1", tags=["SmartClaim Autopilot"])
```

This registers the following endpoints:

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/autopilot/process/{claim_id}` | Run pipeline |
| `GET` | `/api/v1/autopilot/run/{run_id}` | Fetch run |
| `GET` | `/api/v1/autopilot/claim/{claim_id}/runs` | List runs for claim |
| `POST` | `/api/v1/autopilot/override/{claim_id}` | Human override (GR-4) |
| `GET` | `/api/v1/autopilot/drift` | Drift monitor stats |
| `POST` | `/api/v1/autopilot/drift/snapshot` | Persist drift snapshot |

---

## Environment Variables

All variables use the `FEATURE12_` prefix.  See `.env.feature-12.example` for
descriptions and defaults.

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | _(required)_ | Shared with ZoneGuard core |
| `FEATURE12_LLM_MODEL` | `claude-sonnet-4-6` | Claude model for decisions |
| `FEATURE12_LLM_MAX_TOKENS` | `1024` | LLM response token cap |
| `FEATURE12_SHADOW_MODE` | `true` | Process but don't apply decisions |
| `FEATURE12_SHADOW_CONFIDENCE_MIN` | `0.50` | Shadow band lower bound |
| `FEATURE12_SHADOW_CONFIDENCE_MAX` | `0.80` | Shadow band upper bound |
| `FEATURE12_CONFIDENCE_ESCALATION_THRESHOLD` | `0.80` | GR-2 confidence gate |
| `FEATURE12_AUDIT_DIR` | `./audit_logs/feature_12` | GR-3 audit log directory |
| `FEATURE12_DRIFT_WINDOW_SIZE` | `100` | GR-5 sliding window size |
| `FEATURE12_DRIFT_ALERT_THRESHOLD` | `0.20` | GR-5 rate-delta alert trigger |

---

## Pipeline Overview

```
POST /api/v1/autopilot/process/{claim_id}
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  AutopilotService.process_claim(claim_id)               │
│                                                         │
│  Step 1 ── Signal Validation                            │
│    Read QuadSignal rows; compute avg confidence         │
│    Shadow-mode gate applied here                        │
│                                                         │
│  Step 2 ── FraudShield Score                            │
│    Import FraudShield (read-only); call .evaluate()     │
│    Updates claim.fraud_score                            │
│                                                         │
│  Step 3 ── On-Chain Formula Validation (mock)           │
│    _mock_onchain_validate() computes parametric payout  │
│    Replace body with ZoneChain adapter when live        │
│                                                         │
│  Step 4 ── LLM Structured Decision                      │
│    AutopilotLLMClient.decide() → claude-sonnet-4-6      │
│    Required JSON: {decision, confidence,                │
│                    reasoning, payout_amount}            │
│                                                         │
│  Guard Rails (all 5 applied after Step 4)               │
│    GR-1  Formula enforcement (payout locked)            │
│    GR-2  Confidence gate → ESCALATE if < 80%            │
│    GR-3  Immutable reasoning snapshot                   │
│    GR-4  Human override (event-driven via endpoint)     │
│    GR-5  Drift monitor record + alert check             │
│                                                         │
│  Step 5 ── IPFS Audit Log (local file stub)             │
│    Writes {audit_dir}/{claim_id}/{run_id}.json          │
│    CID field reserved for future IPFS pinning           │
└─────────────────────────────────────────────────────────┘
```

---

## Guard Rails Detail

### GR-1 — Formula Enforcement
`FormulaEnforcementRail` compares `llm_output.payout_amount` to the
`calculated_payout` from Step 3.  Any deviation beyond `$0.01` is logged and
the formula value is used unconditionally.  The LLM system prompt also
instructs the model to return the formula payout, providing a double layer of
enforcement.

### GR-2 — Confidence Gate
`ConfidenceGateRail` checks `llm_output.confidence` against
`FEATURE12_CONFIDENCE_ESCALATION_THRESHOLD` (default 0.80).  If the confidence
is below the threshold the decision is overridden to `ESCALATE` regardless of
what the LLM returned.

### GR-3 — Immutable Reasoning Audit
`ImmutableReasoningAuditRail` captures the full LLM output — raw JSON
response, token counts, latency, model name, and reasoning — into the guard
rail audit payload.  This is unconditional: the reasoning is stored even for
rejected or escalated claims.  The payload is written to the IPFS audit log in
Step 5.

### GR-4 — Human Override Endpoint
`POST /api/v1/autopilot/override/{claim_id}` accepts `override_decision`,
`override_reason`, `overridden_by`, and optional `notes`.  `HumanOverrideRail`
validates the payload and the router persists an `AutopilotOverride` row.
The original autopilot decision is preserved for audit; the claim status update
is left to the claims service.

### GR-5 — Statistical Drift Monitor
`StatisticalDriftMonitor` maintains an in-process sliding deque of size
`FEATURE12_DRIFT_WINDOW_SIZE` (default 100).  After each full window, approval,
rejection, and escalation rates are compared to the previous window.  If any
rate shifts by more than `FEATURE12_DRIFT_ALERT_THRESHOLD` (default 0.20), a
structured alert dict is returned and logged at `WARNING` level.  Snapshots can
be persisted to `f12_drift_snapshots` via `POST /api/v1/autopilot/drift/snapshot`.

---

## Shadow Mode

When `FEATURE12_SHADOW_MODE=true` (the default):

1. Only claims whose `avg_signal_confidence` falls in
   `[FEATURE12_SHADOW_CONFIDENCE_MIN, FEATURE12_SHADOW_CONFIDENCE_MAX]` are
   processed (MEDIUM-confidence band).
2. The full pipeline runs and the decision is logged to `f12_autopilot_runs`
   with `is_shadow=true` and `shadow_decision` populated.
3. The underlying `Claim` row status is **not** changed.
4. The IPFS audit log is still written for observability.

To promote to live mode, set `FEATURE12_SHADOW_MODE=false`.

---

## Future Work / TODOs

- [ ] Replace `_mock_onchain_validate()` with real ZoneChain adapter
- [ ] Replace local file audit log with IPFS HTTP API pinning (Step 5)
- [ ] Wire `StatisticalDriftMonitor` to Redis for multi-instance deployments
- [ ] Add Alembic migration for `f12_*` tables
- [ ] Add Prometheus metrics for pipeline latency and guard-rail trigger rates
- [ ] Implement async pipeline variant using `asyncio` + Anthropic async client
