# Only export the models that actually exist
from app.models.hosted_automation import HostedAutomation, AutomationRun

__all__ = [
    "HostedAutomation",
    "AutomationRun",
]
