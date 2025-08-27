from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from datetime import datetime, timezone

Base = declarative_base()

def now_utc():
    return datetime.now(timezone.utc)

class Run(Base):
    __tablename__ = "runs"
    run_id = Column(String(40), primary_key=True)
    user = Column(String(128), nullable=True)
    workflow_id = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="queued")
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    inputs = Column(JSON, nullable=True)
    params = Column(JSON, nullable=True)
    output_preview = Column(Text, nullable=True)

class Workflow(Base):
    __tablename__ = "workflows"
    workflow_id = Column(String(128), primary_key=True)
    name = Column(String(255), nullable=False)
    adapter = Column(String(64), nullable=False, default="langflow")
    config = Column(JSON, nullable=False, default=dict)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)
