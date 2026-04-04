from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from db.database import Base
import uuid


class PolicyExclusionType(Base):
    __tablename__ = "policy_exclusion_types"

    id = Column(String, primary_key=True)  # e.g. "WAR"
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # "standard", "operational", "behavioral"
    check_phase = Column(String, nullable=False)  # "policy_creation", "claim_trigger", "claim_review"


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=lambda: f"POL-{uuid.uuid4().hex[:8].upper()}")
    rider_id = Column(String, ForeignKey("riders.id"), nullable=False)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    status = Column(String, nullable=False, default="active")  # active, expired, cancelled
    weekly_premium = Column(Float, nullable=False)
    max_payout = Column(Float, nullable=False)
    coverage_start = Column(DateTime(timezone=True), nullable=False)
    coverage_end = Column(DateTime(timezone=True), nullable=False)
    is_forward_locked = Column(Boolean, default=False)  # Forward Premium Lock (8% discount)
    forward_lock_weeks = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PolicyAppliedExclusion(Base):
    __tablename__ = "policy_applied_exclusions"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    policy_id = Column(String, ForeignKey("policies.id"), nullable=False)
    exclusion_type_id = Column(String, ForeignKey("policy_exclusion_types.id"), nullable=False)
    is_active = Column(Boolean, default=True)
