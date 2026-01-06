from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class AutomationType(str, Enum):
    WEBSITE_MONITOR = "website_monitor"
    PRICE_TRACKER = "price_tracker"
    DISCORD_NOTIFIER = "discord_notifier"
    SLACK_NOTIFIER = "slack_notifier"
    EMAIL_DIGEST = "email_digest"

class AutomationStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"

class TaskInput(BaseModel):
    task_description: str = Field(..., min_length=10, max_length=1000)
    automation_type: Optional[AutomationType] = None

class AutomationConfig(BaseModel):
    name: str
    description: str
    type: AutomationType
    config: Dict[str, Any]
    schedule: Optional[str] = "*/30 * * * *"  # Default: every 30 mins

class AutomationResponse(BaseModel):
    id: str
    name: str
    type: AutomationType
    status: AutomationStatus
    config: Dict[str, Any]
    workflow_code: str
    created_at: datetime
    next_run: Optional[datetime] = None

class WorkflowDesign(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    description: str
    estimated_tokens: int

class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str
