from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class WorkflowDesign(BaseModel):
    task_description: str
    automation_type: str

@router.post("/design")
def design_workflow(workflow: WorkflowDesign):
    """Design workflow endpoint (simplified for MVP)"""
    return {
        "message": "Workflow design endpoint",
        "task": workflow.task_description,
        "type": workflow.automation_type,
        "status": "success"
    }

@router.get("/status")
def get_status():
    """Health check for workflows"""
    return {"status": "online", "service": "workflows"}
