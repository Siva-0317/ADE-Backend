from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class HostedAutomation(Base):
    __tablename__ = "hosted_automations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, default="demo_user")
    automation_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    config = Column(Text, nullable=False)
    interval_minutes = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    last_result = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class AutomationRun(Base):
    __tablename__ = "automation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    automation_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    result = Column(Text, nullable=True)
    notified = Column(Boolean, default=False)
    executed_at = Column(DateTime, server_default=func.now())
