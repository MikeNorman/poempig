#!/usr/bin/env python3
"""
Robust Poem Scraper
- Ensures at least 50 poems per poet
- Tracks success rates and coverage
- Multiple fallback strategies for poem detection
"""

import time
import json
import requests
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class RobustWorker:
    """Robust worker that ensures minimum poem count"""
    
    def __init__(self, delay: float = 3.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.scraped_urls = set()
        self.load_scraped_urls()
        self.stats = {
            'poets_processed': 0,
            'poems_found': 0,
            'poets_with_50_plus': 0,
            'total_poems_available': 0,
            'coverage_percentage': 0.0
        }
    
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
    
    def extract_total_poems(self, soup) -> Optional[int]:
        """Extract total poem count from My poems link"""
        my_poems_links = soup.find_all('a', string=lambda text: text and 'My poems' in text)
        if my_poems_links:
            my_poems_text = my_poems_links[0].get_text()
            match = re.search(r'My poems \((\d+(?:,\d+)*)\)', my_poems_text)
            if match:
                return int(match.group(1).replace(',', ''))
        return None
    
    def find_poems_aggressive(self, soup, poet_url: str) -> List[Dict]:
        """Use multiple strategies to find poems"""
        poems = []
        
        # Strategy 1: author_link_list containers (preview section)
        author_link_lists = soup.find_all('div', class_='author_link_list')
        if author_link_lists:
            print(f"📋 Strategy 1: Found {len(author_link_lists)} author_link_list containers")
            for container in author_link_lists:
                links = container.find_all('a')
                for link in links:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    if self.is_valid_poem_link(href, title):
                        poem_url = urljoin(poet_url, href)
                        poems.append({'title': title, 'url': poem_url})
        
        # Strategy 2: Look for any links with poem in URL
        if len(poems) < 50:
            print(f"📋 Strategy 2: Looking for poem links in URLs")
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                if ('/poem/' in href or 'poem' in href.lower()) and self.is_valid_poem_link(href, title):
                    poem_url = urljoin(poet_url, href)
                    poems.append({'title': title, 'url': poem_url})
        
        # Strategy 3: Look for any relative links that might be poems
        if len(poems) < 50:
            print(f"📋 Strategy 3: Looking for relative links")
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                if (href.startswith('/') and not href.startswith('/classics/') and 
                    not href.startswith('/login') and not href.startswith('/register') and
                    len(title) > 3 and self.is_valid_poem_link(href, title)):
                    poem_url = urljoin(poet_url, href)
                    poems.append({'title': title, 'url': poem_url})
        
        # Remove duplicates
        seen_urls = set()
        unique_poems = []
        for poem in poems:
            if poem['url'] not in seen_urls:
                seen_urls.add(poem['url'])
                unique_poems.append(poem)
        
        return unique_poems
    
    def is_valid_poem_link(self, href: str, title: str) -> bool:
        """Check if a link is likely a poem"""
        if not href or not title or len(title) < 3:
            return False
        
        # Skip obvious non-poem links
        skip_words = ['login', 'register', 'help', 'follow', 'add to', 'edit', 'delete',
                     'share', 'tweet', 'facebook', 'twitter', 'instagram', 'home', 'about',
                     'contact', 'privacy', 'terms', 'next', 'previous', 'page', 'full title list']
        
        if any(skip in title.lower() for skip in skip_words):
            return False
        
        if href.startswith('/classics/') or href.startswith('http') or href.startswith('#'):
            return False
        
        return True
    
    def scrape_poet_poems(self, poet_url: str) -> List[Dict]:
        """Scrape all poems from a poet page with aggressive detection"""
        print(f"\n📖 Scraping poet: {poet_url}")
        
        try:
            time.sleep(self.delay)
            response = self.session.get(poet_url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Error fetching poet page: {e}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract total poem count
        total_poems = self.extract_total_poems(soup)
        if total_poems:
            print(f"📊 Total poems available: {total_poems:,}")
            self.stats['total_poems_available'] += total_poems
        
        # Find poems using multiple strategies
        poems = self.find_poems_aggressive(soup, poet_url)
        
        print(f"✅ Found {len(poems)} poems")
        
        # Check if we met the 50-poem minimum
        if len(poems) >= 50:
            print(f"🎯 SUCCESS: Got {len(poems)} poems (≥50 minimum)")
            self.stats['poets_with_50_plus'] += 1
        else:
            print(f"⚠️ WARNING: Only got {len(poems)} poems (<50 minimum)")
        
        # Show coverage
        if total_poems:
            coverage = (len(poems) / total_poems) * 100
            print(f"📈 Coverage: {len(poems)}/{total_poems:,} poems ({coverage:.1f}%)")
        
        self.stats['poems_found'] += len(poems)
        self.stats['poets_processed'] += 1
        
        return poems
    
    def scrape_poem(self, poem_url: str) -> Optional[Dict]:
        """Scrape individual poem content"""
        try:
            time.sleep(self.delay)
            response = self.session.get(poem_url, timeout=10)
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
    
    def print_stats(self):
        """Print final statistics"""
        print(f"\n{'='*60}")
        print(f"📊 FINAL STATISTICS")
        print(f"{'='*60}")
        print(f"Poets processed: {self.stats['poets_processed']}")
        print(f"Poems found: {self.stats['poems_found']:,}")
        print(f"Poets with 50+ poems: {self.stats['poets_with_50_plus']}")
        print(f"Success rate: {self.stats['poets_with_50_plus']}/{self.stats['poets_processed']} ({self.stats['poets_with_50_plus']/max(1, self.stats['poets_processed'])*100:.1f}%)")
        if self.stats['total_poems_available'] > 0:
            overall_coverage = (self.stats['poems_found'] / self.stats['total_poems_available']) * 100
            print(f"Overall coverage: {self.stats['poems_found']:,}/{self.stats['total_poems_available']:,} ({overall_coverage:.1f}%)")

def main():
    """Test robust scraper"""
    
    # Your poet URLs
    test_poets = [
        "https://allpoetry.com/William-Butler-Yeats",
        "https://allpoetry.com/e.e.-cummings/",
        "https://allpoetry.com/Robert-Frost",
        "https://allpoetry.com/Langston-Hughes",
        "https://allpoetry.com/Emily-Dickinson"
    ]
    
    # Create robust worker
    worker = RobustWorker(delay=3.0)
    
    all_poems = []
    start_time = time.time()
    
    print(f"🚀 Starting Robust Scraper")
    print(f"📖 {len(test_poets)} poets to scrape")
    print(f"🎯 Target: At least 50 poems per poet")
    print(f"⏱️ 3-second delay between requests")
    
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
    
    elapsed = time.time() - start_time
    print(f"\n🎉 Scraping complete!")
    print(f"📊 Total poems: {len(all_poems)}")
    print(f"⏱️ Time elapsed: {elapsed:.1f} seconds")
    print(f"📈 Rate: {len(all_poems)/elapsed*60:.1f} poems/minute")
    
    # Print final statistics
    worker.print_stats()
    
    # Save to JSONL for ingestion
    if all_poems:
        with open('scraped_poems.jsonl', 'a') as f:
            for poem in all_poems:
                f.write(json.dumps(poem) + '\n')
        print(f"💾 Added {len(all_poems)} new poems to scraped_poems.jsonl")

if __name__ == "__main__":
    main()
