from sqlalchemy import Column, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.database import Base
from datetime import datetime, timezone
import uuid


class PremiumPayment(Base):
    """Records of premium payments made by riders for their policies."""
    __tablename__ = "premium_payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rider_id = Column(String, ForeignKey("riders.id"), nullable=False)
    policy_id = Column(String, ForeignKey("policies.id"), nullable=False)
    amount = Column(Float, nullable=False)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    status = Column(String, default="paid")  # pending, paid, failed
    payment_method = Column(String, default="UPI")
    transaction_ref = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
