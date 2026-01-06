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

PRODUCT_URL = "{product_url}"
WEBHOOK_URL = "{webhook_url}"
TARGET_PRICE = {target_price}

def extract_price(url):
    """Extract price from product page"""
    headers = {{
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }}
    
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Try common price selectors
    price_selectors = [
        '.price', '#priceblock_dealprice', '#priceblock_ourprice',
        '.a-price-whole', '[data-price]', '.product-price'
    ]
    
    for selector in price_selectors:
        element = soup.select_one(selector)
        if element:
            price_text = element.get_text()
            # Extract numeric price
            match = re.search(r'[0-9,]+\\.?[0-9]*', price_text)
            if match:
                return float(match.group().replace(',', ''))
    
    return None

def notify_price_drop(url, current_price, target_price):
    """Send price alert notification"""
    message = f"""
🎉 **Price Drop Alert!**
Product: {{url}}
Current Price: ₹{{current_price}}
Target Price: ₹{{target_price}}
Savings: ₹{{target_price - current_price}}
    """
    payload = {{"content": message}}
    requests.post(WEBHOOK_URL, json=payload)

def main():
    """Main price tracking logic"""
    current_price = extract_price(PRODUCT_URL)
    
    if current_price:
        print(f"Current price: ₹{{current_price}}")
        
        if TARGET_PRICE > 0 and current_price <= TARGET_PRICE:
            notify_price_drop(PRODUCT_URL, current_price, TARGET_PRICE)
            print("Price alert sent!")
        else:
            print(f"Price still above target (₹{{TARGET_PRICE}})")
    else:
        print("Failed to extract price")

if __name__ == "__main__":
    main()
'''
    return code
