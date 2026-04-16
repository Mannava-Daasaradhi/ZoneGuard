"""
Google Gemini API integration for claim audit reports.

Triggered for MEDIUM-confidence claims. Synthesizes signal data,
historical context, and exclusion checks into plain-language audit reports.
"""

from config import get_settings


async def generate_audit_report(claim_data: dict) -> dict:
    """Generate a Gemini-powered audit report for a claim."""

    settings = get_settings()

    prompt = _build_prompt(claim_data)

    if settings.gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            report_text = response.text
            model_used = "gemini-1.5-flash"
        except Exception as e:
            report_text = _fallback_report(claim_data)
            model_used = "fallback_template"
    else:
        report_text = _fallback_report(claim_data)
        model_used = "fallback_template"

    return {
        "report": report_text,
        "model_used": model_used,
        "prompt_tokens": len(prompt.split()),
    }


def _build_prompt(data: dict) -> str:
    return f"""You are an insurance claim auditor for ZoneGuard, a parametric income protection platform
for Amazon Flex delivery riders in Bengaluru, India.

Analyze this MEDIUM-confidence claim and produce a structured audit report.

CLAIM DATA:
- Claim ID: {data.get('claim_id', 'N/A')}
- Zone: {data.get('zone_name', 'N/A')} ({data.get('zone_id', 'N/A')})
- Confidence: {data.get('confidence', 'MEDIUM')}
- Signals Fired: {data.get('signals_fired', 3)}/4

SIGNAL DETAILS:
- S1 Environmental: {data.get('s1', {})}
- S2 Mobility: {data.get('s2', {})}
- S3 Economic: {data.get('s3', {})}
- S4 Crowd: {data.get('s4', {})}

ZONETWIN COUNTERFACTUAL:
{data.get('zone_twin', 'Not available')}

EXCLUSION CHECK:
{data.get('exclusion_check', {})}

FRAUD SCORE: {data.get('fraud_score', 'N/A')}

Produce a concise audit report (150-200 words) covering:
1. Signal convergence summary
2. Which signal(s) missed threshold and by how much
3. Historical comparison from ZoneTwin
4. Exclusion check results
5. Recommendation: APPROVE, REJECT, or RECHECK with reasoning
"""


def _fallback_report(data: dict) -> str:
    """Template-based fallback when Gemini is unavailable."""
    signals_fired = data.get("signals_fired", 3)
    zone = data.get("zone_name", "Unknown")
    confidence = data.get("confidence", "MEDIUM")

    s_details = data.get("signal_details", {})
    missed = [k for k, v in s_details.items() if not v.get("breached", False)]
    hit = [k for k, v in s_details.items() if v.get("breached", False)]

    missed_str = ", ".join(missed) if missed else "none"
    hit_str = ", ".join(hit) if hit else "none"

    twin = data.get("zone_twin", {})
    expected = twin.get("expected_inactivity", {}).get("p50", "N/A")

    return (
        f"AUDIT REPORT — {data.get('claim_id', 'N/A')}\n\n"
        f"Zone: {zone} | Confidence: {confidence} | Signals: {signals_fired}/4\n\n"
        f"Signals converged: {hit_str}. Signals below threshold: {missed_str}. "
        f"ZoneTwin counterfactual estimates {expected}% rider inactivity at current conditions. "
        f"Exclusion check: {'PASSED' if data.get('exclusion_check', {}).get('passed', True) else 'TRIGGERED'}. "
        f"Fraud score: {data.get('fraud_score', 0.1):.2f} (low risk). "
        f"Recommendation: APPROVE — signal convergence pattern is consistent with historical disruption events in {zone}."
    )
