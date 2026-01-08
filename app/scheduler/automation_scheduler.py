from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import httpx
import json
import os
from bs4 import BeautifulSoup
from app.database import SessionLocal
from app.models.hosted_automation import HostedAutomation, AutomationRun

# Email setup with detailed checks
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_ENABLED = False

if RESEND_API_KEY:
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        EMAIL_ENABLED = True
        print(f"✅ Resend configured with key: {RESEND_API_KEY[:10]}...")
    except ImportError:
        print("❌ Resend package not installed!")
else:
    print("❌ RESEND_API_KEY not found in environment!")

scheduler = BackgroundScheduler()

def send_email_notification(email: str, subject: str, url: str, content: str):
    """Send email via Resend"""
    if not EMAIL_ENABLED:
        print(f"❌ Cannot send email - EMAIL_ENABLED={EMAIL_ENABLED}")
        return
    
    try:
        print(f"📧 Sending email to: {email}")
        print(f"   Subject: {subject}")
        
        import resend
        
        params = {
            "from": "Agentic Automation <onboarding@resend.dev>",
            "to": [email],
            "subject": subject,
            "html": f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ padding: 30px; }}
        .alert {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .url {{ color: #667eea; word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0; }}
        .preview {{ background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 15px 0; max-height: 200px; overflow: auto; }}
        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 Change Detected!</h1>
        </div>
        <div class="content">
            <div class="alert">
                <strong>Your automation detected a change</strong>
            </div>
            
            <h3>Monitored URL:</h3>
            <div class="url">{url}</div>
            
            <h3>New Content Preview:</h3>
            <div class="preview"><pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">{content[:400]}</pre></div>
            
            <p style="color: #666; margin-top: 20px;">
                Visit your automation dashboard to see full details and manage your automations.
            </p>
        </div>
        <div class="footer">
            <p><strong>Agentic Automation Platform</strong></p>
            <p>You're receiving this because you set up an automation to monitor this URL.</p>
            <p style="margin-top: 10px;">
                <a href="https://your-frontend.vercel.app/hosted-automations" style="color: #667eea;">Manage Automations →</a>
            </p>
        </div>
    </div>
</body>
</html>
            """
        }
        
        result = resend.Emails.send(params)
        print(f"✅ Email sent successfully!")
        print(f"   Resend response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Email send failed!")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def send_discord_notification(webhook_url: str, title: str, content: str):
    """Send Discord notification"""
    try:
        response = httpx.post(webhook_url, json={
            "embeds": [{
                "title": title,
                "description": content,
                "color": 5814783,
                "timestamp": datetime.now().isoformat(),
                "footer": {"text": "Agentic Automation Platform"}
            }]
        }, timeout=5.0)
        
        if response.status_code == 204:
            print(f"✅ Discord notification sent!")
            return True
        else:
            print(f"❌ Discord failed: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Discord error: {e}")
        return False

def execute_website_monitor(automation: HostedAutomation, db):
    """Execute website monitoring automation"""
    try:
        config = json.loads(automation.config)
        
        print(f"\n{'='*60}")
        print(f"🔄 Executing automation #{automation.id}: {automation.name}")
        print(f"   URL: {config.get('url')}")
        print(f"   Discord: {'✓' if config.get('discord_webhook') else '✗'}")
        print(f"   Email: {config.get('email', 'Not set')}")
        print(f"{'='*60}\n")
        
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
        
        db.commit()
        
        # Send notifications if changed
        notifications_sent = []
        
        if changed:
            print(f"🔥 CHANGE DETECTED!")
            
            # Discord
            if config.get('discord_webhook'):
                success = send_discord_notification(
                    config['discord_webhook'],
                    f"🔔 Change detected: {automation.name}",
                    f"**URL:** {config['url']}\n\n**New content:**\n{current_value[:300]}"
                )
                if success:
                    notifications_sent.append("Discord")
            
            # Email
            if config.get('email'):
                print(f"\n📧 EMAIL NOTIFICATION:")
                print(f"   Recipient: {config['email']}")
                print(f"   EMAIL_ENABLED: {EMAIL_ENABLED}")
                
                if EMAIL_ENABLED:
                    success = send_email_notification(
                        config['email'],
                        f"🔔 Change Detected: {automation.name}",
                        config['url'],
                        current_value[:500]
                    )
                    if success:
                        notifications_sent.append("Email")
                        run.notified = True
                        db.commit()
                else:
                    print(f"   ⚠️  Email disabled - check RESEND_API_KEY")
            
            print(f"\n✅ Notifications sent: {', '.join(notifications_sent) if notifications_sent else 'None'}")
        else:
            print(f"✓ No change detected")
        
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Automation execution error: {e}")
        import traceback
        print(traceback.format_exc())
        
        run = AutomationRun(
            automation_id=automation.id,
            status="error",
            result=str(e)[:500],
            notified=False
        )
        db.add(run)
        db.commit()

def run_scheduled_automations():
    """Main scheduler loop"""
    db = SessionLocal()
    
    try:
        # Get active automations
        automations = db.query(HostedAutomation).filter(
            HostedAutomation.is_active == True
        ).all()
        
        if not automations:
            print("⏸️  No active automations")
            return
        
        print(f"\n🔍 Found {len(automations)} active automation(s):")
        for auto in automations:
            config = json.loads(auto.config)
            print(f"   #{auto.id}: {auto.name} (Email: {config.get('email', 'none')})")
        
        # Check each automation
        for automation in automations:
            # Demo mode: run every 10 seconds minimum
            if automation.last_run:
                seconds_since = (datetime.now() - automation.last_run).total_seconds()
                if seconds_since < 10:
                    continue
            
            # Execute
            if automation.automation_type == "website_monitor":
                execute_website_monitor(automation, db)
                
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        db.close()

def start_scheduler():
    """Start background scheduler"""
    print("\n" + "="*60)
    print("🚀 STARTING AUTOMATION SCHEDULER")
    print("="*60)
    print(f"Mode: Demo (every 10 seconds)")
    print(f"Email: {'✅ ENABLED' if EMAIL_ENABLED else '❌ DISABLED'}")
    if EMAIL_ENABLED:
        print(f"Resend API Key: {RESEND_API_KEY[:15]}...")
    print("="*60 + "\n")
    
    scheduler.add_job(
        run_scheduled_automations,
        trigger=IntervalTrigger(seconds=10),
        id='automation_checker',
        name='Check automations every 10s',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ Scheduler running!\n")

def shutdown_scheduler():
    """Stop scheduler"""
    scheduler.shutdown()
    print("✅ Scheduler stopped")
