def generate_code(config: dict) -> str:
    """Generate Discord notification code"""
    
    webhook_url = config.get("webhook_url")
    message_template = config.get("message_template", "Notification: {content}")
    data_source = config.get("data_source", "")
    
    code = f'''
import requests
import json
from datetime import datetime

WEBHOOK_URL = "{webhook_url}"
MESSAGE_TEMPLATE = "{message_template}"
DATA_SOURCE = "{data_source}"

def fetch_data():
    """Fetch data from source"""
    if DATA_SOURCE:
        response = requests.get(DATA_SOURCE, timeout=10)
        return response.json() if response.status_code == 200 else {{}}
    return {{}}

def send_discord_notification(content):
    """Send message to Discord via webhook"""
    payload = {{
        "content": content,
        "username": "Automation Bot",
        "embeds": [{{
            "title": "Automated Notification",
            "description": content,
            "color": 3447003,
            "timestamp": datetime.utcnow().isoformat()
        }}]
    }}
    
    response = requests.post(WEBHOOK_URL, json=payload)
    return response.status_code == 204

def main():
    """Main execution"""
    data = fetch_data()
    message = MESSAGE_TEMPLATE.format(content=str(data), time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    if send_discord_notification(message):
        print(f"Notification sent successfully at {{datetime.now()}}")
    else:
        print("Failed to send notification")

if __name__ == "__main__":
    main()
'''
    return code
