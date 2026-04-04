from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from db.database import Base
import uuid


class PremiumCalculation(Base):
    __tablename__ = "premium_calculations"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    rider_id = Column(String, ForeignKey("riders.id"), nullable=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    risk_score = Column(Integer, nullable=False)
    premium_amount = Column(Float, nullable=False)
    factor_breakdown = Column(JSON, nullable=False)
    # { disruption_freq: {weight: 0.35, score: 72, contribution: 25.2}, ... }
    premium_tier = Column(String, nullable=False)  # ₹29, ₹49, ₹69, ₹99
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
