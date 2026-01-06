from app.models import AutomationConfig, AutomationType
from app.utils.llm_client import call_llm
from app.templates import website_monitor, price_tracker, discord_notifier

async def generate_automation_code(automation: AutomationConfig) -> str:
    """Generate executable Python code for automation"""
    
    # Use templates for common automations
    if automation.type == AutomationType.WEBSITE_MONITOR:
        return website_monitor.generate_code(automation.config)
    elif automation.type == AutomationType.PRICE_TRACKER:
        return price_tracker.generate_code(automation.config)
    elif automation.type == AutomationType.DISCORD_NOTIFIER:
        return discord_notifier.generate_code(automation.config)
    
    # For custom automations, use LLM
    prompt = f"""Generate production-ready Python code for this automation:

Name: {automation.name}
Type: {automation.type}
Config: {automation.config}

Requirements:
1. Use only free APIs (no paid services)
2. Include error handling and logging
3. Must be executable as standalone script
4. Add retry logic for network calls
5. Use environment variables for secrets

Return ONLY the Python code, no explanations.
"""
    
    code = await call_llm(prompt)
    return code
