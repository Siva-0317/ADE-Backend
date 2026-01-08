from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
import json

from app.database import get_db
from app.models.hosted_automation import HostedAutomation, AutomationRun

router = APIRouter()

class CreateHostedAutomation(BaseModel):
    automation_type: str
    name: str
    config: dict
    interval_minutes: int = 60

class HostedAutomationResponse(BaseModel):
    id: int
    automation_type: str
    name: str
    config: dict
    interval_minutes: int
    is_active: bool
    last_run: datetime | None
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/create", response_model=HostedAutomationResponse)
def create_hosted_automation(
    automation: CreateHostedAutomation,
    db: Session = Depends(get_db)
):
    """Create a new cloud-hosted automation"""
    
    # For MVP, limit to 3 automations per user (implement user_id from auth later)
    user_id = "demo_user"  # Replace with actual auth
    
    count = db.query(HostedAutomation).filter(
        HostedAutomation.user_id == user_id
    ).count()
    
    if count >= 3:
        raise HTTPException(
            status_code=400,
            detail="Free tier limited to 3 active automations"
        )
    
    new_automation = HostedAutomation(
        user_id=user_id,
        automation_type=automation.automation_type,
        name=automation.name,
        config=json.dumps(automation.config),
        interval_minutes=automation.interval_minutes,
        is_active=True
    )
    
    db.add(new_automation)
    db.commit()
    db.refresh(new_automation)
    
    # Parse config back to dict for response
    result = HostedAutomationResponse.from_orm(new_automation)
    result.config = json.loads(new_automation.config)
    
    return result

@router.get("/list", response_model=List[HostedAutomationResponse])
def list_hosted_automations(db: Session = Depends(get_db)):
    """Get all automations for current user"""
    user_id = "demo_user"  # Replace with actual auth
    
    automations = db.query(HostedAutomation).filter(
        HostedAutomation.user_id == user_id
    ).order_by(HostedAutomation.created_at.desc()).all()
    
    results = []
    for auto in automations:
        result = HostedAutomationResponse.from_orm(auto)
        result.config = json.loads(auto.config)
        results.append(result)
    
    return results

@router.put("/{automation_id}/toggle")
def toggle_automation(automation_id: int, db: Session = Depends(get_db)):
    """Pause or resume an automation"""
    automation = db.query(HostedAutomation).filter(
        HostedAutomation.id == automation_id
    ).first()
    
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    automation.is_active = not automation.is_active
    db.commit()
    
    return {"id": automation_id, "is_active": automation.is_active}

@router.delete("/{automation_id}")
def delete_automation(automation_id: int, db: Session = Depends(get_db)):
    """Delete an automation"""
    automation = db.query(HostedAutomation).filter(
        HostedAutomation.id == automation_id
    ).first()
    
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    db.delete(automation)
    db.commit()
    
    return {"message": "Automation deleted successfully"}

@router.get("/{automation_id}/runs")
def get_automation_runs(
    automation_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get execution history for an automation"""
    runs = db.query(AutomationRun).filter(
        AutomationRun.automation_id == automation_id
    ).order_by(AutomationRun.executed_at.desc()).limit(limit).all()
    
    return runs
