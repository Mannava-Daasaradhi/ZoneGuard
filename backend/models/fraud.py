from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from db.database import Base
import uuid


class FraudFlag(Base):
    __tablename__ = "fraud_flags"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    claim_id = Column(String, ForeignKey("claims.id"), nullable=False)
    rider_id = Column(String, ForeignKey("riders.id"), nullable=False)
    score = Column(Float, nullable=False)  # 0.0 to 1.0
    risk_level = Column(String, nullable=False)  # low, review, hold
    features = Column(JSON, default=dict)  # feature vector used for scoring
    created_at = Column(DateTime(timezone=True), server_default=func.now())
