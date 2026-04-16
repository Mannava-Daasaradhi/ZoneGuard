"""
Dummy UPI payout gateway simulator.
"""

import logging
import uuid
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def process_payout(rider_id: str, amount: float, upi_id: str = None) -> dict:
    """Simulate UPI payout processing with a short delay."""

    upi_ref = f"ZG-2026-{uuid.uuid4().hex[:8].upper()}"

    # Simulate processing delay (2 seconds)
    await asyncio.sleep(2)

    # 95% success rate
    import random
    success = random.random() < 0.95

    if not success:
        logger.warning(f"Payout {upi_ref} for rider {rider_id} failed (gateway timeout)")

    return {
        "upi_ref": upi_ref,
        "amount": amount,
        "rider_id": rider_id,
        "upi_id": upi_id or f"{rider_id.lower()}@upi",
        "status": "settled" if success else "failed",
        "gateway": "simulated_razorpay",
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "gateway_response": {
            "transaction_id": upi_ref,
            "status_code": 200 if success else 503,
            "message": "Payment successful" if success else "Gateway timeout — retry scheduled",
        },
    }
