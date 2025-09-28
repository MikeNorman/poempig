#!/usr/bin/env python3
"""
Auto VPN Scraper - Integrates OpenVPN rotation with poem scraping
"""

import time
import json
import requests
from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from vpn_rotator import OpenVPNRotator

class AutoVPNWorker:
    """Worker with automatic VPN rotation"""
    
    def __init__(self, delay: float = 3.0, rotate_every: int = 5):
        self.delay = delay
        self.rotate_every = rotate_every
        self.request_count = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.scraped_urls = set()
        self.vpn_rotator = None
        self.load_scraped_urls()
        
        # Initialize VPN rotator
        try:
            self.vpn_rotator = OpenVPNRotator()
            print("🔧 VPN rotator initialized")
        except FileNotFoundError:
            print("⚠️ No OpenVPN configs found - running without VPN rotation")
    
    def load_scraped_urls(self):
        """Load already scraped URLs from the main output file"""
        try:
            with open('scraped_poems.jsonl', 'r') as f:
                for line in f:
                    data = json.loads(line.strip())
                    if 'source_url' in data:
                        self.scraped_urls.add(data['source_url'])
            print(f"📋 Loaded {len(self.scraped_urls)} already scraped URLs")
        except FileNotFoundError:
            print("📋 No previous poems found, starting fresh")
    
    def make_request(self, url):
        """Make request with automatic VPN rotation"""
        self.request_count += 1
        
        # Rotate VPN every N requests
        if self.vpn_rotator and self.request_count % self.rotate_every == 0:
            print(f"🔄 Rotating VPN (request #{self.request_count})")
            if not self.vpn_rotator.rotate():
                print("⚠️ VPN rotation failed, continuing anyway")
            time.sleep(2)  # Wait for VPN to stabilize
        
        time.sleep(self.delay)
        return self.session.get(url, timeout=10)
    
    def scrape_poet_poems(self, poet_url: str) -> List[Dict]:
        """Scrape all poems from a poet page"""
        print(f"📖 Scraping poet: {poet_url}")
        
        try:
            response = self.make_request(poet_url)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Error fetching poet page: {e}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract total poem count
        total_poems = None
        my_poems_links = soup.find_all('a', string=lambda text: text and 'My poems' in text)
        if my_poems_links:
            my_poems_text = my_poems_links[0].get_text()
            import re
            match = re.search(r'My poems \((\d+(?:,\d+)*)\)', my_poems_text)
            if match:
                total_poems = int(match.group(1).replace(',', ''))
                print(f"📊 Total poems available: {total_poems:,}")
        
        # Find poem links
        poem_links = []
        author_link_lists = soup.find_all('div', class_='author_link_list')
        if author_link_lists:
            print(f"📋 Found {len(author_link_lists)} author_link_list containers")
            for i, container in enumerate(author_link_lists):
                links = container.find_all('a')
                poem_links.extend(links)
                print(f"🔗 Container {i+1} has {len(links)} links")
        
        print(f"📊 Total links found from preview: {len(poem_links)}")
        
        # Filter and create poem objects
        poems = []
        for link in poem_links:
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            if (href and title and len(title) > 2 and
                not href.startswith('/classics/') and
                not href.startswith('http') and
                not href.startswith('#') and
                'Full title list' not in title and
                'Follow' not in title):
                
                poem_url = urljoin(poet_url, href)
                poems.append({'title': title, 'url': poem_url})
        
        print(f"✅ Found {len(poems)} poems")
        
        if total_poems:
            coverage = (len(poems) / total_poems) * 100
            print(f"📈 Coverage: {len(poems)}/{total_poems:,} poems ({coverage:.1f}%)")
        
        return poems
    
    def scrape_poem(self, poem_url: str) -> Optional[Dict]:
        """Scrape individual poem content"""
        try:
            response = self.make_request(poem_url)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Error fetching poem: {e}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract poem title
        title = "Untitled"
        title_elem = soup.find('h1') or soup.find('h2')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Extract author
        author = "Unknown"
        follow_buttons = soup.find_all('a', string=lambda text: text and 'Follow' in text)
        for follow_btn in follow_buttons:
            parent = follow_btn.parent
            if parent:
                author_text = parent.get_text(strip=True)
                if 'Follow' in author_text:
                    author = author_text.split('Follow')[0].strip()
                    if author and len(author) > 2:
                        break
        
        # Extract poem text
        poem_text = ""
        title_container = soup.find('h1') or soup.find('h2')
        if title_container:
            poem_container = title_container.find_next('div')
            if poem_container:
                container_text = poem_container.get_text(separator='\n', strip=True)
                lines = container_text.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if any(skip in line.lower() for skip in ['follow', 'add to list', 'login', 'register', 'help', 'poems', 'write', 'groups', 'contests', 'publish', 'store']):
                        continue
                    if len(line) < 3:
                        continue
                    if line in ['•', '|', '→', '←']:
                        continue
                    cleaned_lines.append(line)
                poem_text = '\n'.join(cleaned_lines)
        
        if not poem_text or len(poem_text.strip()) < 20:
            return None
        
        return {
            'title': title,
            'author': author,
            'text': poem_text,
            'source_url': poem_url
        }

def main():
    """Test auto VPN scraper"""
    
    # Your poet URLs
    test_poets = [
        "https://allpoetry.com/William-Butler-Yeats",
        "https://allpoetry.com/e.e.-cummings/",
        "https://allpoetry.com/Robert-Frost",
        "https://allpoetry.com/Langston-Hughes",
        "https://allpoetry.com/Emily-Dickinson"
    ]
    
    # Create auto VPN worker
    worker = AutoVPNWorker(delay=3.0, rotate_every=5)
    
    all_poems = []
    start_time = time.time()
    
    print(f"🚀 Starting Auto VPN Scraper")
    print(f"📖 {len(test_poets)} poets to scrape")
    print(f"🔄 Rotating VPN every {worker.rotate_every} requests")
    print(f"⏱️ 3-second delay between requests")
    
    try:
        for i, poet_url in enumerate(test_poets):
            print(f"\n--- Poet {i+1}/{len(test_poets)} ---")
            
            # Get poem list
            poems = worker.scrape_poet_poems(poet_url)
            
            # Scrape first 10 poems from each poet for testing
            new_poems = 0
            skipped_poems = 0
            
            for j, poem in enumerate(poems[:10]):
                if poem['url'] in worker.scraped_urls:
                    print(f"⏭️ Skipping already scraped: {poem['title']}")
                    skipped_poems += 1
                    continue
                    
                print(f"📝 Scraping poem {j+1}: {poem['title']}")
                poem_data = worker.scrape_poem(poem['url'])
                if poem_data:
                    all_poems.append(poem_data)
                    new_poems += 1
                    print(f"✅ Got: {poem_data['title']} by {poem_data['author']}")
                else:
                    print(f"❌ Failed to scrape: {poem['title']}")
            
            print(f"📊 Poet summary: {new_poems} new poems, {skipped_poems} already scraped")
    
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
    finally:
        if worker.vpn_rotator:
            worker.vpn_rotator.cleanup()
    
    elapsed = time.time() - start_time
    print(f"\n🎉 Scraping complete!")
    print(f"📊 Total poems: {len(all_poems)}")
    print(f"⏱️ Time elapsed: {elapsed:.1f} seconds")
    print(f"📈 Rate: {len(all_poems)/elapsed*60:.1f} poems/minute")
    
    # Save to JSONL for ingestion
    if all_poems:
        with open('scraped_poems.jsonl', 'a') as f:
            for poem in all_poems:
                f.write(json.dumps(poem) + '\n')
        print(f"💾 Added {len(all_poems)} new poems to scraped_poems.jsonl")

if __name__ == "__main__":
    main()
