"""
Test the complete poet workflow: poet page -> poem list -> individual poems
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from poem_scraper import ItemScraper
from scraper_ingestion import scrape_and_ingest_url

def test_poet_workflow():
    """Test scraping a poet's page to get their poems"""
    
    # Known poet URLs from AllPoetry
    poet_urls = [
        "https://allpoetry.com/Charles-Bukowski",
        "https://allpoetry.com/Emily-Dickinson", 
        "https://allpoetry.com/Robert-Frost",
        "https://allpoetry.com/William-Shakespeare",
        "https://allpoetry.com/Pablo-Neruda"
    ]
    
    scraper = ItemScraper()
    total_poems_ingested = 0
    
    for i, poet_url in enumerate(poet_urls, 1):
        print(f"\n🎭 Poet {i}/{len(poet_urls)}: {poet_url}")
        
        try:
            # Get poems from this poet
            poems = scraper.scrape_allpoetry_poet_poems(poet_url)
            print(f"   📖 Found {len(poems)} poems")
            
            if not poems:
                print(f"   ⚠️  No poems found for this poet")
                continue
            
            # Scrape first 3 poems from this poet (to avoid too many requests)
            for j, poem in enumerate(poems[:3], 1):
                print(f"   📝 Poem {j}: {poem['title'][:50]}...")
                
                try:
                    # Scrape the individual poem
                    poem_data = scraper.scrape_allpoetry_poem(poem['url'])
                    if poem_data:
                        # Ingest the poem
                        count = scrape_and_ingest_url(poem_data['source_url'], f"AllPoetry - {poet_url}")
                        total_poems_ingested += count
                        print(f"      ✅ Ingested: {poem_data['title']} by {poem_data['author']}")
                    else:
                        print(f"      ❌ Failed to scrape poem")
                    
                    # Add delay to be respectful
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"      ❌ Error scraping poem: {e}")
                    continue
            
            # Add delay between poets
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Error with poet {poet_url}: {e}")
            continue
    
    print(f"\n🎉 Complete! Ingested {total_poems_ingested} poems total")

if __name__ == "__main__":
    test_poet_workflow()
