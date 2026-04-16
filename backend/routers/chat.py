from fastapi import APIRouter
from pydantic import BaseModel
from config import get_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

SYSTEM_PROMPT = """You are ZoneGuard Assistant, an AI helper for Amazon Flex delivery riders in Bengaluru, India.
ZoneGuard is a parametric income protection platform that covers riders when weather, traffic, or other disruptions prevent them from earning.

Key facts:
- Coverage: flash floods, severe AQI (>300), transport strikes, heat waves, road closures
- 4-signal fusion: Environmental (S1), Mobility (S2), Economic (S3), Crowd (S4)
- Payout: 55% of 7-day average daily earnings per disrupted day
- HIGH confidence (4/4 signals) = auto-payout in <2 hours via UPI
- MEDIUM confidence (3/4 signals) = human review within 4 hours
- Premium tiers: ₹39 (low risk), ₹89 (medium), ₹139 (high), ₹225 (flood-prone)
- Max 3 consecutive disruption days covered per week
- 10 standard exclusions (war, pandemic, terrorism, rider misconduct, vehicle defect, pre-existing zone, scheduled maintenance, grace period lapse, fraud, max days exceeded)
- Forward Premium Lock: 4-week commitment = 8% discount

Be helpful, concise, and accurate. Answer in 2-3 sentences when possible. Use ₹ for currency."""


class ChatRequest(BaseModel):
    message: str
    rider_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    source: str


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    """Chat endpoint wrapping Gemini with ZoneGuard system prompt."""
    settings = get_settings()

    if settings.gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                f"{SYSTEM_PROMPT}\n\nUser question: {payload.message}"
            )
            return ChatResponse(response=response.text, source="gemini")
        except Exception as e:
            logger.warning(f"Gemini chat failed: {e}")

    return ChatResponse(response=_fallback_response(payload.message), source="fallback")


def _fallback_response(message: str) -> str:
    msg = message.lower()

    responses = [
        (["claim status", "my claim", "claim update", "status"],
         "Your latest claim is being processed. HIGH confidence claims are auto-paid within 2 hours. Check your dashboard for real-time status."),
        (["payout", "how much", "calculation", "calculated"],
         "Payout = 55% of your 7-day average daily earnings per disrupted day. HIGH confidence = auto-payout via UPI. MEDIUM = reviewed within 4 hours."),
        (["covered", "coverage", "protection", "what events"],
         "ZoneGuard covers: flash floods, severe AQI (>300), transport strikes, heat waves, and road closures. All verified by our 4-signal fusion system."),
        (["exclusion", "not covered", "exception", "excluded"],
         "Exclusions: war, pandemic, terrorism, rider misconduct, vehicle defects, pre-existing zone issues, scheduled maintenance, grace period lapse, and fraud."),
        (["premium", "cost", "price", "how much pay"],
         "Weekly premiums: ₹39 (low risk), ₹89 (medium), ₹139 (high), ₹225 (flood-prone). 4-week Forward Lock = 8% discount. No lock-in otherwise!"),
        (["signal", "quad", "how work", "4 signal"],
         "4 independent signals must converge: S1 Environmental (weather), S2 Mobility (traffic), S3 Economic (orders), S4 Crowd (rider check-ins). 3-4 signals = claim trigger."),
        (["hello", "hi", "hey", "good morning"],
         "Hello! I'm your ZoneGuard Assistant. I can help with claims, payouts, coverage questions, and more. What would you like to know?"),
        (["help", "support", "contact"],
         "I can help with: claim status, payout calculations, coverage details, premium info, and general questions. What do you need?"),
        (["thank", "thanks", "bye"],
         "You're welcome! Stay safe out there. ZoneGuard has your back when disruptions hit."),
    ]

    for keywords, response in responses:
        if any(k in msg for k in keywords):
            return response

    return "I can help with claim status, payouts, coverage, and premium questions. Try asking: 'How is payout calculated?' or 'What events are covered?'"
