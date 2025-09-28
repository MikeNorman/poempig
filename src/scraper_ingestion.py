"""
Simple scraper integration that reuses existing ingestion functions
"""

import json
import tempfile
import os
import sys
from typing import List, Dict

# Add the scripts directory to the path so we can import the existing ingestion function
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))

def scrape_and_ingest_url(url: str, source: str = "Web Scraper") -> int:
    """
    Scrape a URL and ingest items using the existing ingestion pipeline
    
    Args:
        url: URL to scrape
        source: Source identifier
        
    Returns:
        Number of items ingested
    """
    try:
        from poem_scraper import ItemScraper
        from ingest_poems import main as ingest_main
        import argparse
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 0
    
    # Scrape the URL using AllPoetry-specific method
    scraper = ItemScraper()
    
    # Check if this is an AllPoetry URL
    if 'allpoetry.com' in url:
        # Use AllPoetry-specific scraper
        poem_data = scraper.scrape_allpoetry_poem(url)
        if not poem_data:
            print(f"❌ Failed to scrape poem from {url}")
            return 0
        
        # Convert to JSONL format
        jsonl_data = [{
            "kind": "poem",
            "title": poem_data.get('title'),
            "author": poem_data.get('author'),
            "text": poem_data.get('text'),
            "source_url": poem_data.get('source_url', url)
        }]
        print(f"📖 Found 1 poem at {url}")
    else:
        # Use generic scraper for other sites
        result = scraper.scrape_url(url)
        
        if result.get('error'):
            print(f"❌ Error scraping {url}: {result['error']}")
            return 0
        
        items = result.get('items', [])
        if not items:
            print(f"⚠️  No items found at {url}")
            return 0
        
        print(f"📖 Found {len(items)} items at {url}")
        
        # Convert scraped items to JSONL format that existing ingestion expects
        jsonl_data = []
        for item in items:
            # Determine kind based on content
            lines = item.get('text', '').split('\n')
            if len(lines) >= 3 and any(len(line.strip()) < 50 for line in lines):
                kind = "poem"
            else:
                kind = "quote"
            
            jsonl_item = {
                "kind": kind,
                "title": item.get('title'),
                "author": item.get('author'),
                "text": item.get('text'),
                "source_url": item.get('source_url', url)
            }
            jsonl_data.append(jsonl_item)
    
    # Write to temporary JSONL file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for item in jsonl_data:
            f.write(json.dumps(item) + '\n')
        temp_file = f.name
    
    try:
        # Use existing ingestion function
        # We need to mock the argparse to call the existing main function
        original_argv = sys.argv
        sys.argv = ['ingest_poems.py', '--input', temp_file, '--source', source]
        
        # Count items before ingestion
        with open(temp_file, 'r') as f:
            before_count = len([line for line in f if line.strip()])
        
        # Run ingestion
        ingest_main()
        
        print(f"✅ Successfully processed {before_count} items from {url}")
        return before_count
        
    finally:
        # Clean up temp file
        os.unlink(temp_file)
        sys.argv = original_argv

def scrape_and_ingest_urls(urls: List[str], source: str = "Web Scraper") -> int:
    """
    Scrape multiple URLs and ingest all items using existing pipeline
    
    Args:
        urls: List of URLs to scrape
        source: Source identifier
        
    Returns:
        Total number of items ingested
    """
    total_ingested = 0
    
    for url in urls:
        print(f"\n🔍 Scraping: {url}")
        count = scrape_and_ingest_url(url, source)
        total_ingested += count
        print(f"   Processed {count} items from this URL")
    
    return total_ingested
