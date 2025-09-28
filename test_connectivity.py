#!/usr/bin/env python3
"""
Test connectivity to AllPoetry without VPN
"""

import requests
from bs4 import BeautifulSoup

def test_connectivity():
    """Test basic connectivity to AllPoetry"""
    print("🔍 Testing connectivity to AllPoetry...")
    
    try:
        # Test basic connection
        response = requests.get('https://allpoetry.com/Charles-Bukowski', timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response Length: {len(response.content)} bytes")
        
        # Test HTML parsing
        soup = BeautifulSoup(response.content, 'html.parser')
        print(f"✅ HTML Parsed Successfully")
        
        # Test poem link detection
        poem_links = soup.select('a[href*="/poem/"]')
        print(f"✅ Found {len(poem_links)} poem links with current selector")
        
        # Test alternative selectors
        alt_links = soup.select('a[href*="poem"]')
        print(f"✅ Found {len(alt_links)} links with 'poem' in href")
        
        # Show first few links
        print("\n📋 First few links found:")
        for i, link in enumerate(poem_links[:5]):
            href = link.get('href', '')
            title = link.get_text(strip=True)
            print(f"  {i+1}. {title} -> {href}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_connectivity()
