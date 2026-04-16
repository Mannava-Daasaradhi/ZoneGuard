from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.database import Base
import uuid


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(String, primary_key=True, default=lambda: f"PAY-{uuid.uuid4().hex[:8].upper()}")
    claim_id = Column(String, ForeignKey("claims.id"), nullable=False)
    rider_id = Column(String, ForeignKey("riders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    upi_ref = Column(String, nullable=False, default=lambda: f"ZG-2026-{uuid.uuid4().hex[:8].upper()}")
    status = Column(String, nullable=False, default="processing")  # processing, settled, failed
    retry_count = Column(Integer, nullable=False, default=0)
    gateway_response = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    settled_at = Column(DateTime(timezone=True), nullable=True)
