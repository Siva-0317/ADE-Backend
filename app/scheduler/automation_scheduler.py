from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import httpx
import json
from bs4 import BeautifulSoup
from app.database import SessionLocal
from app.models.hosted_automation import HostedAutomation, AutomationRun
import asyncio

scheduler = BackgroundScheduler()

async def execute_website_monitor(automation: HostedAutomation):
    """Execute a website monitoring automation"""
    config = json.loads(automation.config)
    db = SessionLocal()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(config['url'], timeout=10.0)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content based on CSS selector
            selector = config.get('css_selector', 'body')
            content = soup.select_one(selector)
            current_value = content.get_text(strip=True) if content else ""
            
            # Compare with last result
            changed = automation.last_result != current_value
            
            # Log run
            run = AutomationRun(
                automation_id=automation.id,
                status="change_detected" if changed else "no_change",
                result=current_value[:500],  # Store first 500 chars
                notified=False
            )
            db.add(run)
            
            # Update automation
            automation.last_run = datetime.now()
            automation.last_result = current_value
            
            # Send notification if changed
            if changed and config.get('discord_webhook'):
                await send_discord_notification(
                    config['discord_webhook'],
                    f"🔔 Change detected on {config['url']}!",
                    current_value[:200]
                )
                run.notified = True
            
            # Send email if configured
            if changed and config.get('email'):
                await send_email_notification(
                    config['email'],
                    f"Website Monitor Alert: {automation.name}",
                    f"Change detected on {config['url']}\n\nNew content:\n{current_value[:300]}"
                )
                run.notified = True
            
            db.commit()
            
    except Exception as e:
        run = AutomationRun(
            automation_id=automation.id,
            status="error",
            result=str(e),
            notified=False
        )
        db.add(run)
        db.commit()
    finally:
        db.close()

async def send_discord_notification(webhook_url: str, title: str, content: str):
    """Send Discord webhook notification"""
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json={
            "embeds": [{
                "title": title,
                "description": content,
                "color": 5814783,
                "timestamp": datetime.now().isoformat()
            }]
        })

async def send_email_notification(email: str, subject: str, body: str):
    """Send email notification using a service like SendGrid/Resend"""
    # Implement with your preferred email service
    pass

def run_scheduled_automations():
    """Main scheduler job that runs active automations"""
    db = SessionLocal()
    
    try:
        # Get all active automations
        automations = db.query(HostedAutomation).filter(
            HostedAutomation.is_active == True
        ).all()
        
        for automation in automations:
            # Check if it's time to run based on interval
            if automation.last_run:
                minutes_since_run = (datetime.now() - automation.last_run).total_seconds() / 60
                if minutes_since_run < automation.interval_minutes:
                    continue
            
            # Execute based on type
            if automation.automation_type == "website_monitor":
                asyncio.run(execute_website_monitor(automation))
            # Add other types here
            
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    # Run every 5 minutes to check for automations to execute
    scheduler.add_job(
        run_scheduled_automations,
        trigger=IntervalTrigger(minutes=5),
        id='automation_checker',
        name='Check and run scheduled automations',
        replace_existing=True
    )
    scheduler.start()

def shutdown_scheduler():
    """Gracefully shutdown scheduler"""
    scheduler.shutdown()
