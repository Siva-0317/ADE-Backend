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
    interval_minutes: int = 10

@router.post("/create")
def create_hosted_automation(
    automation: CreateHostedAutomation,
    db: Session = Depends(get_db)
):
    """Create a new cloud-hosted automation"""
    
    user_id = "demo_user"
    
    # Check limit
    count = db.query(HostedAutomation).filter(
        HostedAutomation.user_id == user_id
    ).count()
    
    print(f"📊 Current automation count: {count}")
    
    if count >= 3:
        raise HTTPException(
            status_code=400,
            detail="Free tier limited to 3 active automations. Delete one to create new."
        )
    
    # Create automation
    new_automation = HostedAutomation(
        user_id=user_id,
        automation_type=automation.automation_type,
        name=automation.name,
        config=json.dumps(automation.config),
        interval_minutes=automation.interval_minutes,
        is_active=True,
        last_run=None,
        last_result=None
    )
    
    db.add(new_automation)
    db.commit()
    db.refresh(new_automation)
    
    print(f"✅ Created automation #{new_automation.id}: {new_automation.name}")
    print(f"   Config: {automation.config}")
    print(f"   Active: {new_automation.is_active}")
    
    return {
        "id": new_automation.id,
        "automation_type": new_automation.automation_type,
        "name": new_automation.name,
        "config": json.loads(new_automation.config),
        "interval_minutes": new_automation.interval_minutes,
        "is_active": new_automation.is_active,
        "last_run": new_automation.last_run,
        "created_at": new_automation.created_at,
        "message": "Automation created successfully! Running every 10 seconds."
    }

@router.get("/list")
def list_hosted_automations(db: Session = Depends(get_db)):
    """Get all automations"""
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

@router.get("/debug")
def debug_automations(db: Session = Depends(get_db)):
    """Debug: See all automations in database"""
    all_automations = db.query(HostedAutomation).all()
    
    return {
        "total_count": len(all_automations),
        "active_count": sum(1 for a in all_automations if a.is_active),
        "automations": [
            {
                "id": a.id,
                "name": a.name,
                "is_active": a.is_active,
                "automation_type": a.automation_type,
                "config": json.loads(a.config),
                "last_run": str(a.last_run) if a.last_run else None,
                "interval_minutes": a.interval_minutes,
                "created_at": str(a.created_at)
            }
            for a in all_automations
        ]
    }

@router.put("/{automation_id}/toggle")
def toggle_automation(automation_id: int, db: Session = Depends(get_db)):
    """Pause or resume automation"""
    automation = db.query(HostedAutomation).filter(
        HostedAutomation.id == automation_id
    ).first()
    
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    automation.is_active = not automation.is_active
    db.commit()
    
    print(f"🔄 Toggled automation #{automation_id}: Active={automation.is_active}")
    
    return {"id": automation_id, "is_active": automation.is_active}

@router.delete("/{automation_id}")
def delete_automation(automation_id: int, db: Session = Depends(get_db)):
    """Delete automation"""
    automation = db.query(HostedAutomation).filter(
        HostedAutomation.id == automation_id
    ).first()
    
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    db.delete(automation)
    db.commit()
    
    print(f"🗑️  Deleted automation #{automation_id}")
    
    return {"message": "Automation deleted successfully"}

@router.get("/{automation_id}/runs")
def get_automation_runs(
    automation_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get execution history"""
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

@router.get("/test-email")
def test_email_service():
    """Test email sending directly"""
    import os
    
    # Check environment
    resend_key = os.getenv("RESEND_API_KEY")
    
    if not resend_key:
        return {
            "error": "RESEND_API_KEY not set in environment",
            "email_enabled": False
        }
    
    try:
        import resend
        resend.api_key = resend_key
        
        # Send test email
        params = {
            "from": "Agentic Automation <onboarding@resend.dev>",
            "to": ["sivaphoton0327@gmail.com"],
            "subject": "Test Email from Agentic Automation",
            "html": "<h1>Success!</h1><p>If you see this, email is working!</p>"
        }
        
        result = resend.Emails.send(params)
        
        return {
            "success": True,
            "message": "Email sent successfully!",
            "resend_response": result,
            "email": "sivaphoton0327@gmail.com"
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
