#!/usr/bin/env python3
"""Test multiple poets to check poem detection consistency"""

import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def test_poet(poet_url, poet_name):
    """Test a single poet"""
    print(f"\n{'='*60}")
    print(f"Testing: {poet_name}")
    print(f"URL: {poet_url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        response = session.get(poet_url, timeout=10)
        response.raise_for_status()
        print(f"✅ Got poet page: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching poet page: {e}")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Count poems in preview section
    author_link_lists = soup.find_all('div', class_='author_link_list')
    preview_poems = 0
    if author_link_lists:
        for container in author_link_lists:
            links = container.find_all('a')
            preview_poems += len(links)
        print(f"📋 Preview section: {len(author_link_lists)} containers, {preview_poems} total links")
    else:
        print(f"📋 Preview section: No author_link_list containers found")
    
    # Count poems in "My poems" page
    my_poems_links = soup.find_all('a', string=lambda text: text and 'My poems' in text)
    if my_poems_links:
        poems_link = my_poems_links[0].get('href')
        print(f"🔗 'My poems' link: {poems_link}")
        
        try:
            time.sleep(1)  # Short delay
            full_poems_url = urljoin(poet_url, poems_link)
            response = session.get(full_poems_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            poem_containers = soup.find_all('div', class_='sub')
            my_poems_count = len(poem_containers)
            print(f"📋 'My poems' page: {my_poems_count} poems")
            
            # Compare
            if preview_poems > my_poems_count:
                print(f"✅ Preview section has MORE poems ({preview_poems} vs {my_poems_count})")
            elif my_poems_count > preview_poems:
                print(f"✅ 'My poems' page has MORE poems ({my_poems_count} vs {preview_poems})")
            else:
                print(f"🤔 Both sections have SAME number of poems ({preview_poems})")
                
        except Exception as e:
            print(f"❌ Error fetching 'My poems' page: {e}")
    else:
        print(f"❌ No 'My poems' link found")

def main():
    """Test multiple poets"""
    poets = [
        ("https://allpoetry.com/e.e.-cummings/", "e.e. cummings"),
        ("https://allpoetry.com/Robert-Frost", "Robert Frost"),
        ("https://allpoetry.com/Langston-Hughes", "Langston Hughes"),
        ("https://allpoetry.com/Emily-Dickinson", "Emily Dickinson")
    ]
    
    print("🧪 Testing poem detection consistency across poets")
    
    for poet_url, poet_name in poets:
        test_poet(poet_url, poet_name)
        time.sleep(2)  # Delay between poets
    
    print(f"\n{'='*60}")
    print("✅ Testing complete!")

if __name__ == "__main__":
    main()
