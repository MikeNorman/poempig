#!/usr/bin/env python3
"""
Scrape famous poets from AllPoetry famous poets page (4 pages)
Much more efficient than A-Z approach
"""

import sys
import os
import time
import json
import re
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from poem_scraper import ItemScraper
from scraper_ingestion import scrape_and_ingest_url
from bs4 import BeautifulSoup

class FamousPoetsScraper:
    """Scrape famous poets from the 4-page famous poets index"""
    
    def __init__(self, delay=5.0):
        self.scraper = ItemScraper(delay=delay)
        self.base_url = "https://allpoetry.com/famous-poets"
        self.poets = []
        self.progress_file = 'famous_poets_progress.json'
        self.progress = self.load_progress()
    
    def load_progress(self):
        """Load existing progress"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'completed_poets': set(),
            'completed_poems': set(),
            'stats': {
                'poets_processed': 0,
                'poems_ingested': 0,
                'errors': 0,
                'start_time': datetime.now().isoformat()
            }
        }
    
    def save_progress(self):
        """Save current progress"""
        progress_to_save = {
            'completed_poets': list(self.progress['completed_poets']),
            'completed_poems': list(self.progress['completed_poems']),
            'stats': self.progress['stats']
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress_to_save, f, indent=2)
    
    def scrape_famous_poets_index(self):
        """Scrape all 4 pages of famous poets"""
        print("🔍 Scraping famous poets index (4 pages)...")
        
        all_poets = []
        
        for page in range(1, 5):  # Pages 1-4
            if page == 1:
                url = self.base_url
            else:
                url = f"{self.base_url}?page={page}"
            
            print(f"   📄 Scraping page {page}: {url}")
            
            try:
                response = self.scraper._make_request(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find poet entries - they have poem counts in parentheses
                poet_entries = soup.find_all('a', href=True)
                
                for entry in poet_entries:
                    href = entry.get('href', '')
                    text = entry.get_text(strip=True)
                    
                    # Look for entries with poem counts like "(165) Charles Bukowski"
                    match = re.match(r'\((\d+)\)\s+(.+)', text)
                    if match:
                        poem_count = int(match.group(1))
                        poet_name = match.group(2)
                        
                        # Skip if it's not a poet link
                        if not href.startswith('/') or href.startswith('/classics/'):
                            continue
                        
                        poet_url = f"https://allpoetry.com{href}"
                        
                        all_poets.append({
                            'name': poet_name,
                            'url': poet_url,
                            'poem_count': poem_count
                        })
                
                print(f"   ✅ Found {len([p for p in all_poets if p['url'].endswith(href.split('/')[-1])])} poets on page {page}")
                time.sleep(self.scraper.delay)
                
            except Exception as e:
                print(f"   ❌ Error scraping page {page}: {e}")
                continue
        
        # Remove duplicates
        seen_urls = set()
        unique_poets = []
        for poet in all_poets:
            if poet['url'] not in seen_urls:
                seen_urls.add(poet['url'])
                unique_poets.append(poet)
        
        self.poets = unique_poets
        print(f"✅ Total famous poets found: {len(unique_poets)}")
        
        # Show top poets by poem count
        sorted_poets = sorted(unique_poets, key=lambda x: x['poem_count'], reverse=True)
        print(f"\n📊 Top 10 poets by poem count:")
        for i, poet in enumerate(sorted_poets[:10], 1):
            print(f"   {i:2d}. {poet['name']} ({poet['poem_count']} poems)")
        
        return unique_poets
    
    def process_poet(self, poet):
        """Process a single poet"""
        poet_url = poet['url']
        poet_name = poet['name']
        expected_poems = poet['poem_count']
        
        if poet_url in self.progress['completed_poets']:
            print(f"⏭️  Skipping {poet_name} (already completed)")
            return True
        
        print(f"\n📖 Processing: {poet_name} (expected {expected_poems} poems)")
        
        try:
            # Get poems for this poet
            poems = self.scraper.scrape_allpoetry_poet_poems(poet_url)
            print(f"   ✅ Found {len(poems)} poems")
            
            if not poems:
                print(f"   ⚠️  No poems found")
                return False
            
            # Process poems
            success_count = 0
            for i, poem in enumerate(poems, 1):
                if poem['url'] in self.progress['completed_poems']:
                    continue
                
                print(f"   📝 {i}/{len(poems)}: {poem['title']}")
                
                try:
                    count = scrape_and_ingest_url(poem['url'], f"AllPoetry Famous - {poet_name}")
                    if count > 0:
                        self.progress['completed_poems'].add(poem['url'])
                        success_count += count
                        print(f"      ✅ Ingested {count} poems")
                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    self.progress['stats']['errors'] += 1
            
            if success_count > 0:
                self.progress['completed_poets'].add(poet_url)
                self.progress['stats']['poets_processed'] += 1
                self.progress['stats']['poems_ingested'] += success_count
                print(f"   ✅ Completed {poet_name}: {success_count} poems ingested")
                return True
            else:
                print(f"   ❌ No poems ingested for {poet_name}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error processing {poet_name}: {e}")
            self.progress['stats']['errors'] += 1
            return False
    
    def run(self, max_poets=None):
        """Run the famous poets scraper"""
        print("🚀 Starting famous poets scraper...")
        
        # Scrape famous poets index
        poets = self.scrape_famous_poets_index()
        
        if max_poets:
            poets = poets[:max_poets]
            print(f"🎯 Limiting to first {max_poets} poets")
        
        # Process poets
        for i, poet in enumerate(poets, 1):
            print(f"\n--- Poet {i}/{len(poets)} ---")
            
            self.process_poet(poet)
            
            # Save progress every 5 poets
            if i % 5 == 0:
                self.save_progress()
                print(f"\n📊 Progress saved: {len(self.progress['completed_poets'])} poets completed")
            
            time.sleep(self.scraper.delay)
        
        # Final save
        self.save_progress()
        
        print(f"\n🎉 Famous poets scraping complete!")
        print(f"📊 Final stats:")
        print(f"   Poets processed: {len(self.progress['completed_poets'])}")
        print(f"   Poems ingested: {len(self.progress['completed_poems'])}")
        print(f"   Errors: {self.progress['stats']['errors']}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape famous poets from AllPoetry")
    parser.add_argument("--max", type=int, help="Maximum poets to process")
    parser.add_argument("--delay", type=float, default=5.0, help="Delay between requests")
    
    args = parser.parse_args()
    
    scraper = FamousPoetsScraper(delay=args.delay)
    scraper.run(max_poets=args.max)

if __name__ == "__main__":
    main()
