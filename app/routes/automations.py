from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from app.models import AutomationConfig, AutomationResponse, AutomationStatus
from app.database import get_supabase
from app.agents.code_generator import generate_automation_code
from app.agents.executor import deploy_automation
from supabase import Client
from datetime import datetime
import uuid

router = APIRouter()

def get_user_from_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    return token

@router.post("/create", response_model=AutomationResponse)
async def create_automation(
    automation: AutomationConfig,
    token: str = Depends(get_user_from_token),
    supabase: Client = Depends(get_supabase)
):
    try:
        # Verify token and get user
        user = supabase.auth.get_user(token)
        user_id = user.user.id
        
        # Generate workflow code
        workflow_code = await generate_automation_code(automation)
        
        # Create automation record
        automation_id = str(uuid.uuid4())
        automation_data = {
            "id": automation_id,
            "user_id": user_id,
            "name": automation.name,
            "description": automation.description,
            "type": automation.type,
            "config": automation.config,
            "workflow_code": workflow_code,
            "status": AutomationStatus.ACTIVE,
            "schedule": automation.schedule,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("automations").insert(automation_data).execute()
        
        # Deploy automation
        deployment_url = await deploy_automation(automation_id, workflow_code, automation.schedule)
        
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

@router.get("/list", response_model=List[AutomationResponse])
async def list_automations(
    token: str = Depends(get_user_from_token),
    supabase: Client = Depends(get_supabase)
):
    try:
        user = supabase.auth.get_user(token)
        user_id = user.user.id
        
        result = supabase.table("automations").select("*").eq("user_id", user_id).execute()
        
        automations = []
        for item in result.data:
            automations.append(AutomationResponse(
                id=item["id"],
                name=item["name"],
                type=item["type"],
                status=item["status"],
                config=item["config"],
                workflow_code=item["workflow_code"],
                created_at=datetime.fromisoformat(item["created_at"])
            ))
        
        return automations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{automation_id}")
async def get_automation(
    automation_id: str,
    token: str = Depends(get_user_from_token),
    supabase: Client = Depends(get_supabase)
):
    try:
        user = supabase.auth.get_user(token)
        user_id = user.user.id
        
        result = supabase.table("automations").select("*").eq("id", automation_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Automation not found")
        
        item = result.data[0]
        return AutomationResponse(
            id=item["id"],
            name=item["name"],
            type=item["type"],
            status=item["status"],
            config=item["config"],
            workflow_code=item["workflow_code"],
            created_at=datetime.fromisoformat(item["created_at"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{automation_id}")
async def delete_automation(
    automation_id: str,
    token: str = Depends(get_user_from_token),
    supabase: Client = Depends(get_supabase)
):
    try:
        user = supabase.auth.get_user(token)
        user_id = user.user.id
        
        result = supabase.table("automations").delete().eq("id", automation_id).eq("user_id", user_id).execute()
        
        return {"message": "Automation deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
