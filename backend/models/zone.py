from sqlalchemy import Column, String, Float, Integer, JSON
from db.database import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(String, primary_key=True)  # e.g. "hsr"
    name = Column(String, nullable=False)
    pin_code = Column(String(6), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    risk_tier = Column(String, nullable=False)  # low, medium, high, flood-prone
    risk_score = Column(Integer, nullable=False, default=50)
    weekly_premium = Column(Integer, nullable=False)
    max_weekly_payout = Column(Integer, nullable=False)
    active_riders = Column(Integer, default=0)
    historical_disruptions = Column(Integer, default=0)
    zone_baselines = Column(JSON, default=dict)  # historical signal baselines
