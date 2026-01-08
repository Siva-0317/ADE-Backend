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

@router.post("/create")
def create_hosted_automation(
    automation: CreateHostedAutomation,
    db: Session = Depends(get_db)
):
    """Create a new cloud-hosted automation"""
    
    user_id = "demo_user"  # For MVP without auth
    
    # Check limit
    count = db.query(HostedAutomation).filter(
        HostedAutomation.user_id == user_id
    ).count()
    
    if count >= 3:
        raise HTTPException(
            status_code=400,
            detail="Free tier limited to 3 active automations. Delete an existing one to create new."
        )
    
    # Create automation
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
    
    return {
        "id": new_automation.id,
        "automation_type": new_automation.automation_type,
        "name": new_automation.name,
        "config": json.loads(new_automation.config),
        "interval_minutes": new_automation.interval_minutes,
        "is_active": new_automation.is_active,
        "last_run": new_automation.last_run,
        "created_at": new_automation.created_at,
        "message": "Automation created successfully! It will run automatically in the cloud."
    }

@router.get("/list")
def list_hosted_automations(db: Session = Depends(get_db)):
    """Get all automations for current user"""
    user_id = "demo_user"
    
    automations = db.query(HostedAutomation).filter(
        HostedAutomation.user_id == user_id
    ).order_by(HostedAutomation.created_at.desc()).all()
    
    results = []
    for auto in automations:
        results.append({
            "id": auto.id,
            "automation_type": auto.automation_type,
            "name": auto.name,
            "config": json.loads(auto.config),
            "interval_minutes": auto.interval_minutes,
            "is_active": auto.is_active,
            "last_run": auto.last_run,
            "created_at": auto.created_at
        })
    
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
    
    return [
        {
            "id": run.id,
            "automation_id": run.automation_id,
            "status": run.status,
            "result": run.result,
            "notified": run.notified,
            "executed_at": run.executed_at
        }
        for run in runs
    ]

@router.get("/debug")
def debug_automations(db: Session = Depends(get_db)):
    """Debug endpoint to see all automations"""
    automations = db.query(HostedAutomation).all()
    
    return {
        "total_count": len(automations),
        "automations": [
            {
                "id": a.id,
                "name": a.name,
                "is_active": a.is_active,
                "automation_type": a.automation_type,
                "config": json.loads(a.config),
                "last_run": str(a.last_run) if a.last_run else None,
                "interval_minutes": a.interval_minutes
            }
            for a in automations
        ]
    }

@router.get("/test-email/{automation_id}")
def test_email(automation_id: int, db: Session = Depends(get_db)):
    """Test email sending for an automation"""
    automation = db.query(HostedAutomation).filter(
        HostedAutomation.id == automation_id
    ).first()
    
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    config = json.loads(automation.config)
    
    if not config.get('email'):
        return {"error": "No email configured in this automation"}
    
    try:
        # Import the email function
        from app.scheduler.automation_scheduler import send_email_notification, EMAIL_ENABLED
        
        if not EMAIL_ENABLED:
            return {
                "error": "Email not enabled",
                "resend_installed": False,
                "api_key_set": False
            }
        
        send_email_notification(
            config['email'],
            f"🧪 Test Email from {automation.name}",
            config['url'],
            "This is a test email to verify your email notifications are working!"
        )
        
        return {
            "success": True,
            "message": f"Test email sent to {config['email']}",
            "email": config['email']
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
