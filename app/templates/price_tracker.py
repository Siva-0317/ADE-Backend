def generate_code(config: dict) -> str:
    """Generate price tracking code"""
    
    product_url = config.get("product_url")
    webhook_url = config.get("webhook_url")
    target_price = config.get("target_price", 0)
    
    code = f'''
import requests
from bs4 import BeautifulSoup
import re
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PRODUCT_URL = "{product_url}"
WEBHOOK_URL = "{webhook_url}"
TARGET_PRICE = {target_price}

def extract_price(url):
    """Extract price from product page"""
    headers = {{
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }}
    
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
    except requests.exceptions.SSLError:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Try common price selectors
    price_selectors = [
        '.price', '#priceblock_dealprice', '#priceblock_ourprice',
        '.a-price-whole', '[data-price]', '.product-price', '._30jeq3'
    ]
    
    for selector in price_selectors:
        element = soup.select_one(selector)
        if element:
            price_text = element.get_text()
            # Extract numeric price
            match = re.search(r'[0-9,]+\\.?[0-9]*', price_text.replace(',', ''))
            if match:
                try:
                    return float(match.group())
                except:
                    continue
    
    return None

def notify_price_drop(url, current_price, target_price):
    """Send price alert notification"""
    savings = target_price - current_price if target_price > current_price else 0
    
    message = f"""
🎉 **Price Drop Alert!**

Product: {{url}}
Current Price: ₹{{current_price:,.2f}}
Target Price: ₹{{target_price:,.2f}}
Savings: ₹{{savings:,.2f}}

Time to buy! 🛒
    """
    
    payload = {{
        "content": message,
        "embeds": [{{
            "title": "💰 Price Alert!",
            "description": f"Price is now ₹{{current_price:,.2f}}",
            "color": 65280,
            "url": url
        }}]
    }}
    
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print("✓ Price alert sent!")
    except Exception as e:
        print(f"Error sending alert: {{e}}")

def main():
    """Main price tracking logic"""
    print(f"Checking price for: {{PRODUCT_URL}}")
    
    current_price = extract_price(PRODUCT_URL)
    
    if current_price:
        print(f"Current price: ₹{{current_price:,.2f}}")
        
        if TARGET_PRICE > 0 and current_price <= TARGET_PRICE:
            notify_price_drop(PRODUCT_URL, current_price, TARGET_PRICE)
            print("🎉 Price is below target!")
        else:
            print(f"Price still above target (₹{{TARGET_PRICE:,.2f}})")
    else:
        print("✗ Failed to extract price")

if __name__ == "__main__":
    main()
'''
    return code
