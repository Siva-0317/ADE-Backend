from fastapi import APIRouter, HTTPException
from app.models import TaskInput, WorkflowDesign
from app.agents.workflow_designer import design_workflow

router = APIRouter()

@router.post("/design", response_model=WorkflowDesign)
async def design_workflow_endpoint(task: TaskInput):
    try:
        workflow = await design_workflow(task.task_description, task.automation_type)
        return workflow
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to design workflow: {str(e)}")
