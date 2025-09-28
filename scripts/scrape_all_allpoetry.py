#!/usr/bin/env python3
"""
Batch scraper to process all AllPoetry poets and ingest all their poems
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import List, Dict

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from poem_scraper import ItemScraper
from scraper_ingestion import scrape_and_ingest_url

class AllPoetryBatchScraper:
    """Batch scraper for AllPoetry with progress tracking and rate limiting"""
    
    def __init__(self, delay: float = 10.0, batch_size: int = 50):
        self.scraper = ItemScraper(delay=delay)
        self.batch_size = batch_size
        self.stats = {
            'poets_processed': 0,
            'poems_scraped': 0,
            'poems_ingested': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        self.progress_file = 'allpoetry_progress.json'
        self.load_progress()
    
    def load_progress(self):
        """Load progress from previous run"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
            print(f"📋 Loaded progress: {self.progress['poets_processed']} poets processed")
        else:
            self.progress = {
                'poets_processed': 0,
                'processed_poets': set(),
                'failed_poets': set()
            }
    
    def save_progress(self):
        """Save current progress"""
        self.progress['poets_processed'] = self.stats['poets_processed']
        self.progress['processed_poets'] = list(self.progress['processed_poets'])
        self.progress['failed_poets'] = list(self.progress['failed_poets'])
        
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def get_all_poets(self) -> List[Dict]:
        """Get all poets from A-Z index"""
        print("🔍 Scraping A-Z poet index...")
        poets = self.scraper.scrape_allpoetry_poet_index()
        print(f"✅ Found {len(poets)} poets total")
        return poets
    
    def process_poet(self, poet: Dict) -> Dict:
        """Process a single poet and return stats"""
        poet_url = poet['url']
        poet_name = poet['name']
        
        # Skip if already processed
        if poet_url in self.progress['processed_poets']:
            return {'skipped': True, 'reason': 'already_processed'}
        
        try:
            print(f"\\n📖 Processing poet: {poet_name}")
            print(f"   URL: {poet_url}")
            
            # Get poems for this poet
            poems = self.scraper.scrape_allpoetry_poet_poems(poet_url)
            print(f"   Found {len(poems)} poems")
            
            if not poems:
                print(f"   ⚠️  No poems found for {poet_name}")
                return {'skipped': True, 'reason': 'no_poems'}
            
            # Process each poem
            poet_stats = {
                'poems_found': len(poems),
                'poems_ingested': 0,
                'poems_failed': 0
            }
            
            for i, poem in enumerate(poems, 1):
                print(f"   📝 Processing poem {i}/{len(poems)}: {poem['title']}")
                
                try:
                    count = scrape_and_ingest_url(poem['url'], f"AllPoetry - {poet_name}")
                    poet_stats['poems_ingested'] += count
                    self.stats['poems_ingested'] += count
                    print(f"      ✅ Ingested {count} poems")
                except Exception as e:
                    print(f"      ❌ Error ingesting poem: {e}")
                    poet_stats['poems_failed'] += 1
                    self.stats['errors'] += 1
            
            # Mark poet as processed
            self.progress['processed_poets'].add(poet_url)
            self.stats['poets_processed'] += 1
            self.stats['poems_scraped'] += len(poems)
            
            print(f"   ✅ Completed {poet_name}: {poem_stats['poems_ingested']} poems ingested")
            return poet_stats
            
        except Exception as e:
            print(f"   ❌ Error processing poet {poet_name}: {e}")
            self.progress['failed_poets'].add(poet_url)
            self.stats['errors'] += 1
            return {'error': str(e)}
    
    def process_batch(self, poets: List[Dict]) -> None:
        """Process a batch of poets"""
        print(f"\\n🚀 Processing batch of {len(poets)} poets...")
        
        for i, poet in enumerate(poets, 1):
            print(f"\\n--- Poet {i}/{len(poets)} ---")
            self.process_poet(poet)
            
            # Save progress every 10 poets
            if i % 10 == 0:
                self.save_progress()
                self.print_stats()
            
            # Add delay between poets
            time.sleep(self.scraper.delay)
    
    def print_stats(self):
        """Print current statistics"""
        elapsed = datetime.now() - self.stats['start_time']
        print(f"\\n📊 Current Statistics:")
        print(f"   Poets processed: {self.stats['poets_processed']}")
        print(f"   Poems scraped: {self.stats['poems_scraped']}")
        print(f"   Poems ingested: {self.stats['poems_ingested']}")
        print(f"   Errors: {self.stats['errors']}")
        print(f"   Elapsed time: {elapsed}")
        
        if self.stats['poets_processed'] > 0:
            avg_time_per_poet = elapsed.total_seconds() / self.stats['poets_processed']
            print(f"   Avg time per poet: {avg_time_per_poet:.1f} seconds")
    
    def run(self, start_from: int = 0, max_poets: int = None):
        """Run the batch scraper"""
        print("🚀 Starting AllPoetry batch scraper...")
        print(f"   Delay between requests: {self.scraper.delay} seconds")
        print(f"   Batch size: {self.batch_size}")
        print(f"   Starting from poet: {start_from}")
        if max_poets:
            print(f"   Max poets to process: {max_poets}")
        
        # Get all poets
        poets = self.get_all_poets()
        
        if start_from > 0:
            poets = poets[start_from:]
            print(f"   Skipping first {start_from} poets")
        
        if max_poets:
            poets = poets[:max_poets]
            print(f"   Limiting to {max_poets} poets")
        
        print(f"   Will process {len(poets)} poets")
        
        # Process in batches
        for i in range(0, len(poets), self.batch_size):
            batch = poets[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(poets) + self.batch_size - 1) // self.batch_size
            
            print(f"\\n🔄 Processing batch {batch_num}/{total_batches}")
            self.process_batch(batch)
            
            # Save progress after each batch
            self.save_progress()
            self.print_stats()
            
            # Break between batches (except for last batch)
            if i + self.batch_size < len(poets):
                print(f"\\n⏸️  Batch complete. Waiting 30 seconds before next batch...")
                time.sleep(30)
        
        print(f"\\n🎉 Batch scraping complete!")
        self.print_stats()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch scrape AllPoetry")
    parser.add_argument("--start", type=int, default=0, help="Start from poet index")
    parser.add_argument("--max", type=int, help="Maximum poets to process")
    parser.add_argument("--delay", type=float, default=10.0, help="Delay between requests (seconds)")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size")
    
    args = parser.parse_args()
    
    scraper = AllPoetryBatchScraper(delay=args.delay, batch_size=args.batch_size)
    scraper.run(start_from=args.start, max_poets=args.max)

if __name__ == "__main__":
    main()
