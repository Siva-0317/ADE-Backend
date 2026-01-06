from app.models import WorkflowDesign, AutomationType
from app.utils.llm_client import call_llm
import json

async def design_workflow(task_description: str, automation_type: AutomationType = None):
    """Design agentic workflow based on task description"""
    
    prompt = f"""You are an expert at designing automation workflows. 
    
Task: {task_description}
Automation Type: {automation_type or 'Auto-detect'}

Design a workflow with these components:
1. Input/Trigger node
2. Processing nodes (data fetch, transform, validate)
3. Action nodes (notify, store, alert)
4. Output node

Return a JSON with:
{{
  "nodes": [
    {{"id": "1", "type": "trigger", "label": "...", "description": "..."}}
  ],
  "edges": [
    {{"source": "1", "target": "2"}}
  ],
  "description": "Overall workflow description",
  "estimated_tokens": 1000
}}

Focus on: monitoring, notification, and data processing tasks.
Use free APIs: Discord webhooks, web scraping, email.
"""
    
    response = await call_llm(prompt)
    
    try:
        workflow_data = json.loads(response)
        return WorkflowDesign(**workflow_data)
    except:
        # Fallback workflow
        return WorkflowDesign(
            nodes=[
                {"id": "1", "type": "trigger", "label": "Start", "description": "Workflow trigger"},
                {"id": "2", "type": "fetch", "label": "Fetch Data", "description": "Get data from source"},
                {"id": "3", "type": "process", "label": "Process", "description": "Transform data"},
                {"id": "4", "type": "notify", "label": "Notify", "description": "Send notification"}
            ],
            edges=[
                {"source": "1", "target": "2"},
                {"source": "2", "target": "3"},
                {"source": "3", "target": "4"}
            ],
            description=f"Automated workflow for: {task_description}",
            estimated_tokens=500
        )
