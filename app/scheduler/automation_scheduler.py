from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import httpx
import json
import os
from bs4 import BeautifulSoup
from app.database import SessionLocal
from app.models.hosted_automation import HostedAutomation, AutomationRun

# Email setup
try:
    import resend
    resend.api_key = os.getenv("RESEND_API_KEY")
    EMAIL_ENABLED = bool(os.getenv("RESEND_API_KEY"))
except ImportError:
    EMAIL_ENABLED = False
    print("⚠️  Resend not installed. Email notifications disabled.")

scheduler = BackgroundScheduler()

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
        
        notifications_sent = []
        
        # Send Discord notification if changed
        if changed and config.get('discord_webhook'):
            send_discord_notification(
                config['discord_webhook'],
                f"🔔 Change detected: {automation.name}",
                f"**URL:** {config['url']}\n\n**New content:**\n{current_value[:300]}"
            )
            notifications_sent.append("Discord")
        
        # Send Email notification if changed
        if changed and config.get('email') and EMAIL_ENABLED:
            send_email_notification(
                config['email'],
                f"🔔 Change Detected: {automation.name}",
                config['url'],
                current_value[:500]
            )
            notifications_sent.append("Email")
        
        if notifications_sent:
            run.notified = True
        
        db.commit()
        
        status_emoji = "🔥" if changed else "✓"
        notif_info = f" ({', '.join(notifications_sent)} sent)" if notifications_sent else ""
        print(f"{status_emoji} Automation #{automation.id}: {automation.name} - {'CHANGED' if changed else 'No change'}{notif_info}")
        
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

def send_email_notification(email: str, subject: str, url: str, content: str):
    """Send email notification using Resend"""
    try:
        params = {
            "from": "Agentic Automation <onboarding@resend.dev>",
            "to": [email],
            "subject": subject,
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                    .alert {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }}
                    .url {{ color: #667eea; word-break: break-all; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2 style="margin: 0;">🔔 Change Detected!</h2>
                    </div>
                    <div class="content">
                        <div class="alert">
                            <strong>Your automation detected a change</strong>
                        </div>
                        
                        <p><strong>Monitored URL:</strong></p>
                        <p class="url">{url}</p>
                        
                        <p><strong>New Content Preview:</strong></p>
                        <pre style="background: white; padding: 15px; border-radius: 5px; overflow-x: auto;">{content}</pre>
                        
                        <p>Visit your <a href="https://your-frontend-url.vercel.app/hosted-automations" style="color: #667eea;">automation dashboard</a> to see full details.</p>
                    </div>
                    <div class="footer">
                        <p>Sent by Agentic Automation Platform</p>
                        <p>You're receiving this because you set up an automation to monitor this URL.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        }
        resend.Emails.send(params)
        print(f"📧 Email sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def run_scheduled_automations():
    """Check and run active automations"""
    db = SessionLocal()
    
    try:
        automations = db.query(HostedAutomation).filter(
            HostedAutomation.is_active == True
        ).all()
        
        if not automations:
            print("⏸️  No active automations to run")
            return
        
        print(f"🔍 Checking {len(automations)} active automation(s)...")
        
        for automation in automations:
            min_interval_seconds = 10  # Demo mode
            
            if automation.last_run:
                seconds_since = (datetime.now() - automation.last_run).total_seconds()
                required_seconds = min(automation.interval_minutes * 60, min_interval_seconds)
                
                if seconds_since < required_seconds:
                    continue
            
            if automation.automation_type == "website_monitor":
                execute_website_monitor(automation, db)
                
    except Exception as e:
        print(f"Scheduler error: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    print("🚀 Starting automation scheduler (Demo mode: checking every 10 seconds)...")
    if EMAIL_ENABLED:
        print("✓ Email notifications enabled via Resend")
    else:
        print("⚠️  Email notifications disabled (no RESEND_API_KEY)")
    
    scheduler.add_job(
        run_scheduled_automations,
        trigger=IntervalTrigger(seconds=10),
        id='automation_checker',
        name='Check automations every 10 seconds (Demo mode)',
        replace_existing=True
    )
    
    scheduler.start()
    print("✓ Scheduler started!")

def shutdown_scheduler():
    """Stop scheduler gracefully"""
    print("Stopping scheduler...")
    scheduler.shutdown()
    print("✓ Scheduler stopped")
