from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from db.database import Base
import uuid


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String, primary_key=True, default=lambda: f"CLM-{uuid.uuid4().hex[:8].upper()}")
    rider_id = Column(String, ForeignKey("riders.id"), nullable=False)
    policy_id = Column(String, ForeignKey("policies.id"), nullable=False)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    disruption_event_id = Column(String, ForeignKey("disruption_events.id"), nullable=False)
    status = Column(String, nullable=False, default="pending_review")
    # pending_review, approved, rejected, paid, held
    confidence = Column(String, nullable=False)
    recommended_payout = Column(Float, nullable=False)
    actual_payout = Column(Float, nullable=True)
    exclusion_check = Column(JSON, default=dict)  # {passed, exclusions_evaluated, exclusions_triggered}
    fraud_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String, nullable=True)
