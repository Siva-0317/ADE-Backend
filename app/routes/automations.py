from fastapi import APIRouter, HTTPException
from typing import List
from app.models import AutomationConfig, AutomationResponse, AutomationStatus
from app.agents.code_generator import generate_automation_code
from app.agents.executor import deploy_automation
from datetime import datetime
import uuid

router = APIRouter()

# NO AUTH FOR MVP - Just generate code!

@router.post("/create", response_model=AutomationResponse)
async def create_automation(automation: AutomationConfig):
    try:
        # Generate workflow code
        workflow_code = await generate_automation_code(automation)
        
        automation_id = str(uuid.uuid4())
        
        return AutomationResponse(
            id=automation_id,
            name=automation.name,
            type=automation.type,
            status=AutomationStatus.ACTIVE,
            config=automation.config,
            workflow_code=workflow_code,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create automation: {str(e)}")

@router.get("/list")
async def list_automations():
    # For MVP, return empty list
    return []

@router.get("/{automation_id}")
async def get_automation(automation_id: str):
    raise HTTPException(status_code=404, detail="Auth not enabled for MVP - code generation only!")
