from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.database import Base


class Rider(Base):
    __tablename__ = "riders"

    id = Column(String, primary_key=True)  # e.g. "AMZFLEX-BLR-04821"
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    weekly_earnings_baseline = Column(Float, default=0)
    tenure_weeks = Column(Integer, default=0)
    kyc_verified = Column(Boolean, default=False)
    upi_id = Column(String, nullable=True)

    # e-Shram integration (Phase 3)
    # NOTE: unique=True is intentionally REMOVED here.
    # Uniqueness for non-NULL values is enforced by the partial index
    # ix_riders_eshram_id in migration 003_eshram_kyc.py.
    # Keeping unique=True AND the partial index would create two overlapping
    # constraints — the full unique constraint treats NULL as a value on some
    # DBs, which would break when multiple unverified riders exist.
    eshram_id = Column(String, nullable=True)               # UAN-format e-Shram ID
    eshram_verified = Column(Boolean, default=False)        # verified via e-Shram portal API
    eshram_income_verified = Column(Boolean, default=False) # earnings baseline cross-checked
    eshram_verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
