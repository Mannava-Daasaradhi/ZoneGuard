from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from db.database import Base
import uuid


class SimulationEvent(Base):
    __tablename__ = "simulation_events"

    id = Column(String, primary_key=True, default=lambda: f"SIM-{uuid.uuid4().hex[:8].upper()}")
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    scenario = Column(String, nullable=False)  # flash_flood, severe_aqi, transport_strike, heat_wave
    signal_overrides = Column(JSON, nullable=False)
    is_active = Column(Integer, default=1)
    triggered_by = Column(String, default="admin")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
