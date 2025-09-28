#!/usr/bin/env python3
"""
macOS NordVPN Scraper - Automated VPN rotation for poem scraping on macOS
Uses NordVPN macOS app's command line interface
"""

import time
import json
import requests
import subprocess
import random
from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class MacOSVPNScraper:
    """Scraper with automated NordVPN rotation for macOS"""
    
    def __init__(self, delay: float = 3.0, rotate_every: int = 5):
        self.delay = delay
        self.rotate_every = rotate_every
        self.request_count = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.scraped_urls = set()
        self.load_scraped_urls()
        
        # Initialize NordVPN
        print("🔧 Initializing NordVPN...")
        self.initialize_VPN()
        print("✅ NordVPN initialized")
    
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
    
    def initialize_VPN(self):
        """Initialize NordVPN connection"""
        try:
            # Check if NordVPN is installed
            result = subprocess.run(['which', 'nordvpn'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ NordVPN CLI not found. Please install NordVPN app from App Store")
                print("   Then enable command line tools in NordVPN settings")
                raise Exception("NordVPN CLI not available")
            
            # Connect to a random server
            self.rotate_VPN()
            
        except Exception as e:
            print(f"⚠️ VPN initialization failed: {e}")
            print("Continuing without VPN...")
    
    def rotate_VPN(self):
        """Rotate to a random NordVPN server"""
        try:
            # List of popular NordVPN server countries
            countries = [
                'United_States', 'Canada', 'United_Kingdom', 'Germany', 
                'France', 'Netherlands', 'Sweden', 'Norway', 'Denmark',
                'Switzerland', 'Austria', 'Belgium', 'Ireland', 'Spain',
                'Italy', 'Poland', 'Czech_Republic', 'Japan', 'Australia',
                'New_Zealand', 'Brazil', 'Mexico', 'Argentina', 'Chile'
            ]
            
            # Pick a random country
            country = random.choice(countries)
            print(f"🌍 Connecting to {country}...")
            
            # Connect to the country
            result = subprocess.run(['nordvpn', 'connect', country], 
                                 capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ Connected to {country}")
                time.sleep(2)  # Wait for connection to stabilize
            else:
                print(f"⚠️ Failed to connect to {country}: {result.stderr}")
                # Try a different country
                country = random.choice(countries)
                print(f"🔄 Trying {country}...")
                result = subprocess.run(['nordvpn', 'connect', country], 
                                     capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"✅ Connected to {country}")
                    time.sleep(2)
                else:
                    print(f"❌ Failed to connect to any server: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            print("⏰ VPN connection timed out")
        except Exception as e:
            print(f"❌ VPN rotation error: {e}")
    
    def make_request(self, url):
        """Make request with automatic VPN rotation"""
        self.request_count += 1
        
        # Rotate VPN every N requests
        if self.request_count % self.rotate_every == 0:
            print(f"🔄 Rotating VPN (request #{self.request_count})")
            try:
                self.rotate_VPN()
                print("✅ VPN rotated successfully")
                time.sleep(3)  # Wait for VPN to stabilize
            except Exception as e:
                print(f"⚠️ VPN rotation failed: {e}")
                print("Continuing with current connection...")
        
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
        
        # Extract total poem count from "My poems (X)" text
        total_poems = None
        my_poems_links = soup.find_all('a', string=lambda text: text and 'My poems' in text)
        if my_poems_links:
            my_poems_text = my_poems_links[0].get_text()
            import re
            match = re.search(r'My poems \((\d+(?:,\d+)*)\)', my_poems_text)
            if match:
                total_poems = int(match.group(1).replace(',', ''))
                print(f"📊 Total poems available: {total_poems:,}")
            else:
                print(f"⚠️ Could not extract poem count from: {my_poems_text}")
        else:
            print(f"⚠️ No 'My poems' link found")
        
        # Find poem links in the page
        poem_links = []
        
        # Find all author_link_list containers - this is where most poems are
        author_link_lists = soup.find_all('div', class_='author_link_list')
        if author_link_lists:
            print(f"📋 Found {len(author_link_lists)} author_link_list containers")
            for i, container in enumerate(author_link_lists):
                links = container.find_all('a')
                poem_links.extend(links)
                print(f"🔗 Container {i+1} has {len(links)} links")
        
        print(f"📊 Total links found from preview: {len(poem_links)}")
        
        # If we have few poems from preview, try the "My poems" page
        if len(poem_links) < 30:
            my_poems_links = soup.find_all('a', string=lambda text: text and 'My poems' in text)
            if my_poems_links:
                poems_link = my_poems_links[0].get('href')
                print(f"🔗 Found 'My poems' link: {poems_link}")
                
                full_poems_url = urljoin(poet_url, poems_link)
                print(f"📋 Fetching full poem list from: {full_poems_url}")
                
                try:
                    response = self.make_request(full_poems_url)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for poems in the full page
                    poem_containers = soup.find_all('div', class_='sub')
                    if poem_containers:
                        print(f"📋 Found {len(poem_containers)} poem containers in full page")
                        for container in poem_containers:
                            title_link = container.find('a', class_='nocolor fn')
                            if title_link:
                                poem_links.append(title_link)
                except Exception as e:
                    print(f"❌ Error fetching full poem list: {e}")
        
        if not poem_links:
            print(f"⚠️ No poem containers found")
        
        poems = []
        for link in poem_links:
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            # Skip only obvious non-poem links
            if (href and title and len(title) > 2 and
                not href.startswith('/classics/') and
                not href.startswith('http') and
                not href.startswith('#') and
                'Full title list' not in title and
                'Follow' not in title):
                
                poem_url = urljoin(poet_url, href)
                poems.append({
                    'title': title,
                    'url': poem_url
                })
        
        print(f"✅ Found {len(poems)} poems")
        
        # Show coverage if we know the total
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
        
        # Extract author - look for text next to a "Follow" button
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
                for sibling in parent.find_previous_siblings():
                    sibling_text = sibling.get_text(strip=True)
                    if sibling_text and len(sibling_text) > 2 and 'Follow' not in sibling_text:
                        author = sibling_text.strip()
                        break
        
        # Extract poem text - look for the main poem content
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
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                if 'Apple Macintosh' in text or 'Radio Shack' in text:
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
    
    def cleanup(self):
        """Clean up VPN connection on exit"""
        print("🔌 Disconnecting VPN...")
        try:
            subprocess.run(['nordvpn', 'disconnect'], capture_output=True, text=True, timeout=10)
            print("✅ VPN disconnected")
        except Exception as e:
            print(f"⚠️ Error disconnecting VPN: {e}")

def main():
    """Test macOS VPN scraper"""
    
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
        "https://allpoetry.com/Pablo-Neruda",
        "https://allpoetry.com/Octavio-Paz",
        "https://allpoetry.com/Oscar-Wilde",
        "https://allpoetry.com/Fernando-Pessoa",
        "https://allpoetry.com/Nizar-Qabbani",
        "https://allpoetry.com/Jose-Marti",
        "https://allpoetry.com/Ernest-Hemingway"
    ]
    
    scraper = None
    all_poems = []
    start_time = time.time()
    
    try:
        # Create macOS VPN scraper
        scraper = MacOSVPNScraper(delay=3.0, rotate_every=5)
        
        print(f"🚀 Starting macOS VPN Scraper")
        print(f"📖 {len(test_poets)} poets to scrape")
        print(f"🔄 Rotating VPN every {scraper.rotate_every} requests")
        print(f"⏱️ 3-second delay between requests")
        
        for i, poet_url in enumerate(test_poets):
            print(f"\n--- Poet {i+1}/{len(test_poets)} ---")
            
            # Get poem list
            poems = scraper.scrape_poet_poems(poet_url)
            
            # Scrape poems from each poet (skip already scraped)
            new_poems = 0
            skipped_poems = 0
            
            for j, poem in enumerate(poems[:50]):  # Test up to 50 poems per poet
                if poem['url'] in scraper.scraped_urls:
                    print(f"⏭️ Skipping already scraped: {poem['title']}")
                    skipped_poems += 1
                    continue
                    
                print(f"📝 Scraping poem {j+1}: {poem['title']}")
                poem_data = scraper.scrape_poem(poem['url'])
                if poem_data:
                    all_poems.append(poem_data)
                    new_poems += 1
                    print(f"✅ Got: {poem_data['title']} by {poem_data['author']}")
                else:
                    print(f"❌ Failed to scrape: {poem['title']}")
            
            print(f"📊 Poet summary: {new_poems} new poems, {skipped_poems} already scraped")
    
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if scraper:
            scraper.cleanup()
    
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
