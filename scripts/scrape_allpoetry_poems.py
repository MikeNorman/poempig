"""
Simple script to scrape AllPoetry poems directly from URLs
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from poem_scraper import ItemScraper
from scraper_ingestion import scrape_and_ingest_url

def scrape_poem_urls(urls, source="AllPoetry.com"):
    """Scrape a list of poem URLs directly"""
    
    print(f"🔍 Scraping {len(urls)} poems from AllPoetry...")
    
    total_ingested = 0
    
    for i, url in enumerate(urls, 1):
        print(f"\n📝 Poem {i}/{len(urls)}: {url}")
        
        try:
            count = scrape_and_ingest_url(url, source)
            total_ingested += count
            print(f"   ✅ Ingested {count} poems")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    print(f"\n🎉 Complete! Ingested {total_ingested} poems total")

def main():
    # Example poem URLs from AllPoetry
    sample_urls = [
        "https://allpoetry.com/16-bit-Intel-8088-chip",
        "https://allpoetry.com/Bluebird",
        "https://allpoetry.com/The-Crunch",
        "https://allpoetry.com/Writing",
        # Add more URLs as needed
    ]
    
    if len(sys.argv) > 1:
        # URLs provided as command line arguments
        urls = sys.argv[1:]
    else:
        # Use sample URLs
        urls = sample_urls
        print("Using sample URLs. Provide URLs as arguments to scrape specific poems.")
    
    scrape_poem_urls(urls)

if __name__ == "__main__":
    main()
