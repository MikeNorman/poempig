#!/usr/bin/env python3
"""
Process manually curated list of poet URLs
Much faster than scraping all poets
"""

import sys
import os
import time
import json
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from poem_scraper import ItemScraper
from scraper_ingestion import scrape_and_ingest_url

class ManualPoetsScraper:
    """Process manually curated list of poets"""
    
    def __init__(self, delay=2.0):  # Faster delay since manual selection
        self.scraper = ItemScraper(delay=delay)
        self.progress_file = 'manual_poets_progress.json'
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
    
    def process_poet(self, poet_url, poet_name=None):
        """Process a single poet"""
        if poet_url in self.progress['completed_poets']:
            print(f"⏭️  Skipping {poet_name or poet_url} (already completed)")
            return True
        
        print(f"\n📖 Processing: {poet_name or poet_url}")
        
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
                    count = scrape_and_ingest_url(poem['url'], f"AllPoetry Manual - {poet_name or 'Unknown'}")
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
                print(f"   ✅ Completed: {success_count} poems ingested")
                return True
            else:
                print(f"   ❌ No poems ingested")
                return False
                
        except Exception as e:
            print(f"   ❌ Error processing: {e}")
            self.progress['stats']['errors'] += 1
            return False
    
    def process_poet_list(self, poets):
        """Process a list of poets"""
        print(f"🚀 Processing {len(poets)} manually curated poets...")
        
        for i, poet in enumerate(poets, 1):
            print(f"\n--- Poet {i}/{len(poets)} ---")
            
            if isinstance(poet, dict):
                poet_url = poet['url']
                poet_name = poet.get('name', 'Unknown')
            else:
                poet_url = poet
                poet_name = 'Unknown'
            
            self.process_poet(poet_url, poet_name)
            
            # Save progress every 3 poets
            if i % 3 == 0:
                self.save_progress()
                print(f"\n📊 Progress saved: {len(self.progress['completed_poets'])} poets completed")
            
            time.sleep(self.scraper.delay)
        
        # Final save
        self.save_progress()
        
        print(f"\n🎉 Manual poets scraping complete!")
        print(f"📊 Final stats:")
        print(f"   Poets processed: {len(self.progress['completed_poets'])}")
        print(f"   Poems ingested: {len(self.progress['completed_poems'])}")
        print(f"   Errors: {self.progress['stats']['errors']}")

def main():
    # Example poet list - replace with your curated list
    poets = [
        {"name": "Charles Bukowski", "url": "https://allpoetry.com/Charles-Bukowski"},
        {"name": "Sylvia Plath", "url": "https://allpoetry.com/Sylvia-Plath"},
        {"name": "William Shakespeare", "url": "https://allpoetry.com/William-Shakespeare"},
        {"name": "Emily Dickinson", "url": "https://allpoetry.com/Emily-Dickinson"},
        {"name": "Robert Frost", "url": "https://allpoetry.com/Robert-Frost"},
        # Add more poets here...
    ]
    
    scraper = ManualPoetsScraper(delay=2.0)  # 2 second delay
    scraper.process_poet_list(poets)

if __name__ == "__main__":
    main()
