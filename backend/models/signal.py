from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from db.database import Base
import uuid


class SignalReading(Base):
    __tablename__ = "signal_readings"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    signal_type = Column(String, nullable=False)  # S1, S2, S3, S4
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    is_breached = Column(Integer, default=0)  # 0 or 1
    raw_data = Column(JSON, default=dict)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())


class DisruptionEvent(Base):
    __tablename__ = "disruption_events"

    id = Column(String, primary_key=True, default=lambda: f"DE-{uuid.uuid4().hex[:8].upper()}")
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    confidence = Column(String, nullable=False)  # HIGH, MEDIUM, LOW, NOISE
    signals_fired = Column(Integer, nullable=False)
    signal_details = Column(JSON, default=dict)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Integer, default=1)
    source = Column(String, default="auto")  # auto, simulator, ndma_override
