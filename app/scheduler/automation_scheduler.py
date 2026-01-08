from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import httpx
import json
from bs4 import BeautifulSoup
from app.database import SessionLocal
from app.models.hosted_automation import HostedAutomation, AutomationRun

scheduler = BackgroundScheduler()

def execute_website_monitor(automation: HostedAutomation, db):
    """Execute a website monitoring automation"""
    try:
        config = json.loads(automation.config)
        
        # Fetch website
        response = httpx.get(config['url'], timeout=10.0, follow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract content
        selector = config.get('css_selector', 'body')
        content = soup.select_one(selector)
        current_value = content.get_text(strip=True) if content else ""
        
        # Check if changed
        changed = automation.last_result != current_value if automation.last_result else True
        
        # Log run
        run = AutomationRun(
            automation_id=automation.id,
            status="change_detected" if changed else "no_change",
            result=current_value[:500],
            notified=False
        )
        db.add(run)
        
        # Update automation
        automation.last_run = datetime.now()
        if changed:
            automation.last_result = current_value
        
        # Send notification if changed
        if changed and config.get('discord_webhook'):
            send_discord_notification(
                config['discord_webhook'],
                f"🔔 Change detected: {automation.name}",
                current_value[:200]
            )
            run.notified = True
        
        db.commit()
        print(f"✓ Executed automation #{automation.id}: {automation.name} - {'CHANGED' if changed else 'No change'}")
        
    except Exception as e:
        print(f"✗ Error executing automation #{automation.id}: {str(e)}")
        run = AutomationRun(
            automation_id=automation.id,
            status="error",
            result=str(e)[:500],
            notified=False
        )
        db.add(run)
        db.commit()

def send_discord_notification(webhook_url: str, title: str, content: str):
    """Send Discord webhook notification"""
    try:
        httpx.post(webhook_url, json={
            "embeds": [{
                "title": title,
                "description": content,
                "color": 5814783,
                "timestamp": datetime.now().isoformat()
            }]
        }, timeout=5.0)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

def run_scheduled_automations():
    """Check and run active automations"""
    db = SessionLocal()
    
    try:
        # Get active automations
        automations = db.query(HostedAutomation).filter(
            HostedAutomation.is_active == True
        ).all()
        
        for automation in automations:
            # Check if it's time to run
            if automation.last_run:
                minutes_since = (datetime.now() - automation.last_run).total_seconds() / 60
                if minutes_since < automation.interval_minutes:
                    continue
            
            # Execute based on type
            if automation.automation_type == "website_monitor":
                execute_website_monitor(automation, db)
                
    except Exception as e:
        print(f"Scheduler error: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    print("🚀 Starting automation scheduler...")
    scheduler.add_job(
        run_scheduled_automations,
        trigger=IntervalTrigger(minutes=5),
        id='automation_checker',
        name='Check automations every 5 minutes',
        replace_existing=True
    )
    scheduler.start()
    print("✓ Scheduler started!")

def shutdown_scheduler():
    """Stop scheduler gracefully"""
    print("Stopping scheduler...")
    scheduler.shutdown()
    print("✓ Scheduler stopped")
