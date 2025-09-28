#!/usr/bin/env python3
"""Test single poet scraping"""

import time
import json
import requests
from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def test_yeats():
    """Test scraping Yeats specifically"""
    poet_url = "https://allpoetry.com/William-Butler-Yeats"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    print(f"📖 Testing poet: {poet_url}")
    
    try:
        response = session.get(poet_url, timeout=10)
        response.raise_for_status()
        print(f"✅ Got poet page: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching poet page: {e}")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Look for the "My poems" link
    my_poems_links = soup.find_all('a', string=lambda text: text and 'My poems' in text)
    print(f"🔍 Found {len(my_poems_links)} 'My poems' links")
    
    if my_poems_links:
        poems_link = my_poems_links[0].get('href')
        print(f"🔗 'My poems' link: {poems_link}")
        
        # Follow the link
        full_poems_url = urljoin(poet_url, poems_link)
        print(f"📋 Fetching: {full_poems_url}")
        
        try:
            response = session.get(full_poems_url, timeout=10)
            response.raise_for_status()
            print(f"✅ Got full poems page: {response.status_code}")
        except Exception as e:
            print(f"❌ Error fetching full poems: {e}")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for poem containers
        poem_containers = soup.find_all('div', class_='sub')
        print(f"📋 Found {len(poem_containers)} 'sub' containers")
        
        # Look for other possible containers
        items_group = soup.find_all('div', class_='items_group')
        print(f"📋 Found {len(items_group)} 'items_group' containers")
        
        # Look for poem links
        poem_links = soup.find_all('a', class_='nocolor fn')
        print(f"📋 Found {len(poem_links)} poem title links")
        
        if poem_links:
            print("First few poem titles:")
            for i, link in enumerate(poem_links[:5]):
                print(f"  {i+1}. {link.get_text(strip=True)}")
    else:
        print("❌ No 'My poems' link found")

if __name__ == "__main__":
    test_yeats()
