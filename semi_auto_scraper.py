#!/usr/bin/env python3
"""
Semi-Automated IP Rotation Scraper
- Runs 3 workers continuously
- Prompts for manual VPN server changes
- Detects IP changes and resumes automatically
"""

import time
import json
import requests
import threading
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

class SemiAutoScraper:
    """Semi-automated scraper with IP rotation prompts"""
    
    def __init__(self, num_workers: int = 1):
        self.num_workers = 1  # Force single worker
        self.workers = []
        self.current_ip = None
        self.rotation_needed = False
        self.paused = False
        
        # Rate limit learning data
        self.rate_limit_data = {
            'ip_history': [],
            'rate_limit_events': [],
            'success_patterns': [],
            'failure_patterns': []
        }
        
        # Single worker config
        worker = SemiAutoWorker(
            worker_id=0,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            delay=3.0,  # 3 second delay between requests
            scraper=self
        )
        self.workers.append(worker)
    
    def get_current_ip(self) -> Optional[str]:
        """Get current public IP"""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=10)
            if response.status_code == 200:
                return response.json().get('ip')
        except:
            pass
        return None
    
    def check_ip_change(self) -> bool:
        """Check if IP has changed (indicating manual VPN switch)"""
        new_ip = self.get_current_ip()
        if new_ip and new_ip != self.current_ip:
            old_ip = self.current_ip
            print(f"🔄 IP changed: {old_ip} → {new_ip}")
            self.current_ip = new_ip
            
            # Record IP change for learning
            self.record_ip_change(old_ip, new_ip)
            return True
        return False
    
    def should_rotate_ip(self) -> bool:
        """Determine if IP rotation is needed"""
        # Check if any worker is getting rate limited
        for worker in self.workers:
            if worker.consecutive_failures >= 3:
                return True
            if worker.rate_limit_count >= 2:
                return True
        
        return False
    
    def check_fresh_ip_after_429(self) -> bool:
        """Check if we have a fresh IP after getting 429'd"""
        print("🔍 Checking if we have a fresh IP after 429 errors...")
        
        # Get current IP
        current_ip = self.get_current_ip()
        if not current_ip:
            print("❌ Could not determine current IP")
            return False
        
        # Check if this IP was used recently (in last 10 minutes)
        recent_ips = []
        for event in self.rate_limit_data.get('rate_limit_events', []):
            if event.get('event_type') == '429_error':
                event_time = datetime.fromisoformat(event['timestamp'])
                if (datetime.now() - event_time).total_seconds() < 600:  # 10 minutes
                    recent_ips.append(event.get('ip'))
        
        if current_ip in recent_ips:
            print(f"⚠️ Current IP {current_ip} was recently blocked (429'd)")
            return False
        
        print(f"✅ Fresh IP detected: {current_ip}")
        return True
    
    def prompt_for_rotation(self):
        """Prompt user to change VPN server"""
        print("\n" + "="*60)
        print("🔄 IP ROTATION NEEDED")
        print("="*60)
        print("Please switch to a different NordVPN server:")
        print("1. Open NordVPN app")
        print("2. Click 'Quick Connect' or choose a different country")
        print("3. Wait for connection to establish")
        print("4. Press ENTER when ready to continue")
        print("="*60)
        
        print("Please switch to a different NordVPN server and press Ctrl+C to stop, then restart the script")
        time.sleep(30)  # Wait 30 seconds instead of user input
        
        # Wait for IP change
        print("⏳ Waiting for IP change detection...")
        for i in range(30):  # Wait up to 30 seconds
            if self.check_ip_change():
                print("✅ IP change detected! Resuming...")
                self.rotation_needed = False
                self.paused = False
                # Reset worker counters
                for worker in self.workers:
                    worker.consecutive_failures = 0
                    worker.rate_limit_count = 0
                return True
            time.sleep(1)
        
        print("⚠️ No IP change detected. Continuing anyway...")
        return False
    
    def scrape_poets_continuous(self, poet_urls: List[str], max_poems_per_poet: int = 20):
        """Continuously scrape poets with IP rotation"""
        print(f"🚀 Starting Semi-Auto Scraper")
        print(f"📖 {len(poet_urls)} poets, {self.num_workers} workers")
        print(f"🔄 Will prompt for VPN rotation when needed")
        
        # Load existing rate limit learning data
        self.load_rate_limit_data()
        
        # Get initial IP
        self.current_ip = self.get_current_ip()
        print(f"📍 Starting IP: {self.current_ip}")
        
        all_poems = []
        start_time = time.time()
        worker = self.workers[0]  # Single worker
        
        try:
            for i, poet_url in enumerate(poet_urls):
                if self.paused:
                    time.sleep(1)
                    continue
                
                print(f"\n[{i+1}/{len(poet_urls)}] Processing: {poet_url}")
                
                # Check if rotation needed
                if self.should_rotate_ip():
                    self.paused = True
                    print("🔄 Rate limits detected, checking for fresh IP...")
                    
                    # Check if we have a fresh IP before prompting for rotation
                    if not self.check_fresh_ip_after_429():
                        print("⚠️ Current IP is not fresh, prompting for rotation...")
                        if not self.prompt_for_rotation():
                            break
                    else:
                        print("✅ Fresh IP detected, resuming...")
                        self.paused = False
                        # Reset worker counters
                        worker.consecutive_failures = 0
                        worker.rate_limit_count = 0
                
                # Scrape this poet
                poems = worker.scrape_poets_batch([poet_url], max_poems_per_poet)
                all_poems.extend(poems)
                
                print(f"📊 Progress: {len(all_poems)} poems scraped, {len(poet_urls)-i-1} poets remaining")
                
                # Save progress
                self.save_progress(poems)
                
                # Save rate limit learning data periodically
                self.save_rate_limit_data()
                
        except KeyboardInterrupt:
            print("\n🛑 Scraping interrupted by user")
        
        end_time = time.time()
        
        print(f"\n📊 Final Results:")
        print(f"   Total poems: {len(all_poems)}")
        print(f"   Time: {end_time - start_time:.1f} seconds")
        print(f"   Poems/hour: {len(all_poems) / ((end_time - start_time) / 3600):.1f}")
        
        return all_poems
    
    def save_progress(self, poems: List[Dict], filename: str = "semi_auto_progress.jsonl"):
        """Save scraped poems to JSONL file"""
        with open(filename, 'a') as f:
            for poem in poems:
                f.write(json.dumps(poem) + '\n')
        print(f"💾 Saved {len(poems)} poems to {filename}")
    
    def save_rate_limit_data(self, filename: str = "rate_limit_learning.json"):
        """Save rate limit learning data"""
        with open(filename, 'w') as f:
            json.dump(self.rate_limit_data, f, indent=2)
        print(f"📊 Saved rate limit learning data to {filename}")
    
    def load_rate_limit_data(self, filename: str = "rate_limit_learning.json"):
        """Load rate limit learning data"""
        try:
            with open(filename, 'r') as f:
                self.rate_limit_data = json.load(f)
            print(f"📊 Loaded rate limit learning data from {filename}")
        except FileNotFoundError:
            print(f"📊 No existing rate limit data found, starting fresh")
    
    def record_rate_limit_event(self, event_type: str, details: Dict):
        """Record a rate limit event for learning"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'ip': self.current_ip,
            'event_type': event_type,
            'details': details
        }
        self.rate_limit_data['rate_limit_events'].append(event)
        
        # Keep only last 100 events
        if len(self.rate_limit_data['rate_limit_events']) > 100:
            self.rate_limit_data['rate_limit_events'] = self.rate_limit_data['rate_limit_events'][-100:]
    
    def record_ip_change(self, old_ip: str, new_ip: str):
        """Record IP change for learning"""
        ip_change = {
            'timestamp': datetime.now().isoformat(),
            'old_ip': old_ip,
            'new_ip': new_ip,
            'success_rate_before': self.get_overall_success_rate()
        }
        self.rate_limit_data['ip_history'].append(ip_change)
    
    def get_overall_success_rate(self) -> float:
        """Calculate overall success rate across all workers"""
        total_requests = sum(worker.total_requests for worker in self.workers)
        successful_requests = sum(worker.successful_requests for worker in self.workers)
        return successful_requests / total_requests if total_requests > 0 else 0.0

class SemiAutoWorker:
    """Worker with rate limit monitoring"""
    
    def __init__(self, worker_id: int, user_agent: str, delay: float, scraper):
        self.worker_id = worker_id
        self.user_agent = user_agent
        self.delay = delay
        self.scraper = scraper
        self.total_requests = 0
        self.successful_requests = 0
        self.consecutive_failures = 0
        self.rate_limit_count = 0
        
        # Create session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        })
    
    def make_request(self, url: str) -> Optional[requests.Response]:
        """Make request with monitoring"""
        try:
            time.sleep(self.delay)
            
            response = self.session.get(url, timeout=10)
            self.total_requests += 1
            
            if response.status_code == 200:
                self.successful_requests += 1
                self.consecutive_failures = 0
                return response
            elif response.status_code == 429:
                self.rate_limit_count += 1
                self.consecutive_failures += 1
                print(f"Worker {self.worker_id}: ⚠️ Rate limited (429)")
                
                # Record rate limit event for learning
                self.scraper.record_rate_limit_event('429_error', {
                    'worker_id': self.worker_id,
                    'url': url,
                    'consecutive_failures': self.consecutive_failures,
                    'rate_limit_count': self.rate_limit_count
                })
                return None
            else:
                self.consecutive_failures += 1
                print(f"Worker {self.worker_id}: ⚠️ HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.consecutive_failures += 1
            print(f"Worker {self.worker_id}: ❌ Request error: {e}")
            return None
    
    def scrape_poet_poems(self, poet_url: str) -> List[Dict]:
        """Scrape poems from a poet"""
        print(f"Worker {self.worker_id}: 📖 Scraping poet: {poet_url}")
        
        response = self.make_request(poet_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        poems = []
        # Find the specific container with poem links
        poem_links = []
        author_link_lists = soup.find_all('div', class_='author_link_list')
        
        if author_link_lists:
            print(f"Worker {self.worker_id}: Found {len(author_link_lists)} author_link_list containers")
            for container in author_link_lists:
                links = container.find_all('a')
                poem_links.extend(links)
                print(f"Worker {self.worker_id}: Container has {len(links)} links")
        else:
            print(f"Worker {self.worker_id}: No author_link_list containers found")
        
        for link in poem_links:
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            # Skip only obvious non-poem links (since we're in the poem container)
            if (href and title and len(title) > 2 and
                not href.startswith('/classics/') and
                not href.startswith('http') and
                not href.startswith('#') and
                'Full title list' not in title):
                
                poem_url = urljoin(poet_url, href)
                poems.append({
                    'title': title,
                    'url': poem_url
                })
        
        print(f"Worker {self.worker_id}: Found {len(poems)} poems")
        return poems
    
    def scrape_poem(self, poem_url: str) -> Optional[Dict]:
        """Scrape individual poem"""
        response = self.make_request(poem_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract poem title - look for the main title
        title = "Untitled"
        title_elem = soup.find('h1') or soup.find('h2')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Extract author - look for text next to a "Follow" button
        author = "Unknown"
        follow_buttons = soup.find_all('a', string=lambda text: text and 'Follow' in text)
        for follow_btn in follow_buttons:
            # Look for author name in the same container or nearby
            parent = follow_btn.parent
            if parent:
                # Look for text in the same element or nearby siblings
                author_text = parent.get_text(strip=True)
                # Extract just the author name (before "Follow")
                if 'Follow' in author_text:
                    author = author_text.split('Follow')[0].strip()
                    if author and len(author) > 2:
                        break
                
                # Also check siblings
                for sibling in parent.find_previous_siblings():
                    sibling_text = sibling.get_text(strip=True)
                    if sibling_text and len(sibling_text) > 2 and 'Follow' not in sibling_text:
                        author = sibling_text.strip()
                        break
        
        # Extract poem text - look for the main poem content
        poem_text = ""
        
        # Find the container that has both title and poem text
        title_container = soup.find('h1') or soup.find('h2')
        if title_container:
            # Look for poem text in the same container or nearby
            poem_container = title_container.find_next('div')
            if poem_container:
                # Get all text from this container
                container_text = poem_container.get_text(separator='\n', strip=True)
                
                # Clean up the text - remove navigation elements
                lines = container_text.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    line = line.strip()
                    # Skip navigation elements
                    if any(skip in line.lower() for skip in ['follow', 'add to list', 'login', 'register', 'help', 'poems', 'write', 'groups', 'contests', 'publish', 'store']):
                        continue
                    # Skip very short lines that are likely navigation
                    if len(line) < 3:
                        continue
                    # Skip lines that look like page structure
                    if line in ['•', '|', '→', '←']:
                        continue
                    
                    cleaned_lines.append(line)
                
                poem_text = '\n'.join(cleaned_lines)
        
        # If we still don't have good poem text, try alternative approach
        if not poem_text or len(poem_text.strip()) < 20:
            # Look for text that contains the poem content
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                if 'Apple Macintosh' in text or 'Radio Shack' in text:  # Known poem content
                    # Clean this text
                    lines = text.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        line = line.strip()
                        if len(line) > 5 and not any(skip in line.lower() for skip in ['follow', 'add to', 'login', 'register']):
                            cleaned_lines.append(line)
                    poem_text = '\n'.join(cleaned_lines)
                    break
        
        if not poem_text or len(poem_text.strip()) < 20:
            return None
        
        return {
            'title': title,
            'author': author,
            'text': poem_text,
            'source_url': poem_url
        }
    
    def scrape_poets_batch(self, poet_urls: List[str], max_poems_per_poet: int = 20) -> List[Dict]:
        """Scrape multiple poets"""
        all_poems = []
        
        for poet_url in poet_urls:
            if self.scraper.paused:
                break
                
            print(f"Worker {self.worker_id}: Processing poet: {poet_url}")
            
            # Get poems for this poet
            poems = self.scrape_poet_poems(poet_url)
            
            # Scrape individual poems
            for poem in poems[:max_poems_per_poet]:
                if self.scraper.paused:
                    break
                    
                print(f"Worker {self.worker_id}: Scraping poem: {poem['title'][:30]}...")
                
                poem_data = self.scrape_poem(poem['url'])
                if poem_data:
                    all_poems.append(poem_data)
                    print(f"Worker {self.worker_id}: ✅ Success")
                else:
                    print(f"Worker {self.worker_id}: ❌ Failed")
        
        return all_poems

def main():
    """Test semi-automated scraper"""
    
    # Your poet URLs
    test_poets = [
            "https://allpoetry.com/William-Butler-Yeats",
            "https://allpoetry.com/e.e.-cummings/",
            "https://allpoetry.com/Robert-Frost",
            "https://allpoetry.com/Langston-Hughes",
            "https://allpoetry.com/Emily-Dickinson",
            "https://allpoetry.com/T-S-Eliot",
            "https://allpoetry.com/Rabindranath-Tagore",
            "https://allpoetry.com/Ogden-Nash",
            "https://allpoetry.com/Khalil-Gibran",
            "https://allpoetry.com/Mewlana-Jalaluddin-Rumi",
            "https://allpoetry.com/William-Blake",
            "https://allpoetry.com/John-Keats",
            "https://allpoetry.com/Walt-Whitman",
            "https://allpoetry.com/Ralph-Waldo-Emerson",
            "https://allpoetry.com/Henry-David-Thoreau",
            "https://allpoetry.com/Kabir",
            "https://allpoetry.com/Percy-Bysshe-Shelley",
            "https://allpoetry.com/Charles-Bukowski",
            "https://allpoetry.com/Sylvia-Plath",
            "https://allpoetry.com/Pablo-Neruda"
        ]
    
    # Create scraper (single worker)
    scraper = SemiAutoScraper(num_workers=1)
    
    # Start scraping
    poems = scraper.scrape_poets_continuous(test_poets, max_poems_per_poet=10)
    
    print(f"\n✅ Scraping complete! Total poems: {len(poems)}")

if __name__ == "__main__":
    main()
