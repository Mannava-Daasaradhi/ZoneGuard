from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.database import Base
import uuid


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    claim_id = Column(String, ForeignKey("claims.id"), nullable=True)
    event_type = Column(String, nullable=False)  # gemini_audit, claim_review, payout_initiated, etc.
    content = Column(Text, nullable=False)
    model_used = Column(String, nullable=True)  # e.g. "gemini-1.5-flash"
    generated_by = Column(String, nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
