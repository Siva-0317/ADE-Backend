from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import httpx
import json
from bs4 import BeautifulSoup
from app.database import SessionLocal
from app.models.hosted_automation import HostedAutomation, AutomationRun

scheduler = BackgroundScheduler()

import os
import resend

# At the top after imports
resend.api_key = os.getenv("RESEND_API_KEY")

def send_email_notification(email: str, subject: str, body: str):
    """Send email notification using Resend"""
    try:
        params = {
            "from": "Agentic Automation <onboarding@resend.dev>",  # Use your domain later
            "to": [email],
            "subject": subject,
            "html": f"""
            <h2>{subject}</h2>
            <p>{body}</p>
            <hr/>
            <small>Sent by Agentic Automation Platform</small>
            """
        }
        resend.Emails.send(params)
        print(f"📧 Email sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def execute_website_monitor(automation: HostedAutomation, db):
    """Execute a website monitoring automation"""
    try:
        config = json.loads(automation.config)
        
        print(f"🔄 Checking automation #{automation.id}: {automation.name}")
        
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
        
        # Send email if configured
        if changed and config.get('email'):
            send_email_notification(
                config['email'],
                f"🔔 Change Detected: {automation.name}",
                f"URL: {config['url']}\n\nNew content:\n{current_value[:300]}"
            )
            run.notified = True

        # Send notification if changed
        if changed and config.get('discord_webhook'):
            send_discord_notification(
                config['discord_webhook'],
                f"🔔 Change detected: {automation.name}",
                f"**URL:** {config['url']}\n\n**New content:**\n{current_value[:300]}"
            )
            run.notified = True
        
        db.commit()
        
        status_emoji = "🔥" if changed else "✓"
        print(f"{status_emoji} Automation #{automation.id}: {automation.name} - {'CHANGED' if changed else 'No change'}")
        
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
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "Agentic Automation Platform"
                }
            }]
        }, timeout=5.0)
        print(f"📨 Discord notification sent!")
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
        
        if not automations:
            print("⏸️  No active automations to run")
            return
        
        print(f"🔍 Checking {len(automations)} active automation(s)...")
        
        for automation in automations:
            # For demo: minimum 10 seconds, otherwise use user's interval
            min_interval_seconds = 10  # Demo mode: 10 seconds minimum
            
            # Check if it's time to run
            if automation.last_run:
                seconds_since = (datetime.now() - automation.last_run).total_seconds()
                # Use whichever is smaller: user interval or minimum for demo
                required_seconds = min(automation.interval_minutes * 60, min_interval_seconds)
                
                if seconds_since < required_seconds:
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
    print("🚀 Starting automation scheduler (Demo mode: checking every 10 seconds)...")
    
    # Check every 10 seconds for demo purposes
    scheduler.add_job(
        run_scheduled_automations,
        trigger=IntervalTrigger(seconds=10),  # Changed from 5 minutes to 10 seconds
        id='automation_checker',
        name='Check automations every 10 seconds (Demo mode)',
        replace_existing=True
    )
    
    scheduler.start()
    print("✓ Scheduler started! Automations will run every 10 seconds minimum")

def shutdown_scheduler():
    """Stop scheduler gracefully"""
    print("Stopping scheduler...")
    scheduler.shutdown()
    print("✓ Scheduler stopped")
