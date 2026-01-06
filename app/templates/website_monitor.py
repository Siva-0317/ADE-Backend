def generate_code(config: dict) -> str:
    """Generate website monitoring code"""
    
    url = config.get("url")
    webhook_url = config.get("webhook_url")
    check_interval = config.get("check_interval", 300)
    css_selector = config.get("css_selector", "body")
    
    code = f'''
import requests
from bs4 import BeautifulSoup
import hashlib
import time
import json

URL = "{url}"
WEBHOOK_URL = "{webhook_url}"
CHECK_INTERVAL = {check_interval}
CSS_SELECTOR = "{css_selector}"
PREVIOUS_HASH_FILE = "website_hash.txt"

def get_content_hash(url, selector):
    """Fetch website content and return hash"""
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    content = soup.select_one(selector)
    if content:
        return hashlib.md5(content.text.encode()).hexdigest()
    return None

def send_notification(message):
    """Send Discord webhook notification"""
    payload = {{"content": message}}
    requests.post(WEBHOOK_URL, json=payload)

def main():
    """Main monitoring loop"""
    # Load previous hash
    try:
        with open(PREVIOUS_HASH_FILE, 'r') as f:
            previous_hash = f.read().strip()
    except FileNotFoundError:
        previous_hash = None
    
    # Get current hash
    current_hash = get_content_hash(URL, CSS_SELECTOR)
    
    if current_hash and current_hash != previous_hash:
        message = f"🔔 Website changed detected!\\n{{URL}}\\nTime: {{time.ctime()}}"
        send_notification(message)
        print(f"Change detected! Previous: {{previous_hash}}, Current: {{current_hash}}")
        
        # Save new hash
        with open(PREVIOUS_HASH_FILE, 'w') as f:
            f.write(current_hash)
    else:
        print(f"No changes detected at {{time.ctime()}}")

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Error: {{e}}")
        time.sleep(CHECK_INTERVAL)
'''
    return code

def validate_config(config: dict) -> bool:
    """Validate website monitor configuration"""
    required_fields = ["url", "webhook_url"]
    return all(field in config for field in required_fields)
