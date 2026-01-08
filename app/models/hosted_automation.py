from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class HostedAutomation(Base):
    __tablename__ = "hosted_automations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # From auth token
    automation_type = Column(String)  # website_monitor, price_tracker, etc
    name = Column(String)
    config = Column(Text)  # JSON config (url, webhook, selector, etc)
    interval_minutes = Column(Integer, default=60)  # Check interval
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    last_result = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
class AutomationRun(Base):
    __tablename__ = "automation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    automation_id = Column(Integer, ForeignKey("hosted_automations.id"))
    status = Column(String)  # success, error, change_detected
    result = Column(Text)  # What changed or error message
    notified = Column(Boolean, default=False)
    executed_at = Column(DateTime, server_default=func.now())
