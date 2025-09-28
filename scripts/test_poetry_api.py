#!/usr/bin/env python3
"""
Test Poetry.com API to see what's available
"""

import requests
import json
import time

def test_poetry_api():
    """Test the Poetry.com API endpoints"""
    base_url = "https://www.poetry.com/api.php"
    
    print("🔍 Testing Poetry.com API...")
    
    # Test different endpoints
    endpoints_to_test = [
        "?action=get_poems",
        "?action=get_authors", 
        "?action=search&query=love",
        "?action=get_poem&id=1",
        "?action=get_author&id=1",
        "?action=get_random_poem",
        "?action=get_popular_poems",
        "?action=get_recent_poems"
    ]
    
    for endpoint in endpoints_to_test:
        url = base_url + endpoint
        print(f"\n📡 Testing: {endpoint}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"   Response (text): {response.text[:200]}...")
            else:
                print(f"   Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   Exception: {e}")
        
        time.sleep(1)  # Be respectful

def test_poetry_com_direct():
    """Test Poetry.com website directly to understand structure"""
    print("\n🔍 Testing Poetry.com website structure...")
    
    try:
        response = requests.get("https://www.poetry.com", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Poetry.com is accessible")
            # Look for API hints in the HTML
            if "api" in response.text.lower():
                print("📡 Found 'api' mentions in HTML")
            if "json" in response.text.lower():
                print("📡 Found 'json' mentions in HTML")
        else:
            print(f"❌ Poetry.com returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing Poetry.com: {e}")

if __name__ == "__main__":
    test_poetry_api()
    test_poetry_com_direct()
