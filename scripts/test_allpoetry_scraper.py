"""
Test script to scrape 10 poets from AllPoetry.com
"""

import os
import sys
import json
import time
from typing import List, Dict

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from poem_scraper import ItemScraper
from scraper_ingestion import scrape_and_ingest_url

def test_allpoetry_scraper():
    """Test scraping 10 poets from AllPoetry"""
    
    print("🔍 Testing AllPoetry scraper with 10 poets...")
    
    scraper = ItemScraper()
    
    # Step 1: Get the poet index
    print("\n📋 Step 1: Scraping poet index...")
    poets = scraper.scrape_allpoetry_poet_index()
    
    if not poets:
        print("❌ No poets found in index")
        return
    
    print(f"✅ Found {len(poets)} poets in index")
    
    # Step 2: Take first 10 poets for testing
    test_poets = poets[:10]
    print(f"\n🎯 Testing with first 10 poets:")
    for i, poet in enumerate(test_poets, 1):
        print(f"  {i}. {poet['name']} - {poet['url']}")
    
    # Step 3: Scrape poems for each poet
    total_poems_scraped = 0
    total_poems_ingested = 0
    
    for i, poet in enumerate(test_poets, 1):
        print(f"\n📖 Step 3.{i}: Scraping poems for {poet['name']}...")
        
        # Get poem list for this poet
        poems = scraper.scrape_allpoetry_poet_poems(poet['url'])
        print(f"   Found {len(poems)} poems")
        
        if not poems:
            print(f"   ⚠️  No poems found for {poet['name']}")
            continue
        
        # Scrape each poem
        poet_poems_scraped = 0
        for j, poem in enumerate(poems[:5], 1):  # Limit to 5 poems per poet for testing
            print(f"   📝 Scraping poem {j}/{min(5, len(poems))}: {poem['title'][:50]}...")
            
            poem_data = scraper.scrape_allpoetry_poem(poem['url'])
            if poem_data:
                poet_poems_scraped += 1
                total_poems_scraped += 1
                
                # Ingest this poem
                print(f"      💾 Ingesting: {poem_data['title']}")
                count = scrape_and_ingest_url(poem_data['source_url'], f"AllPoetry Test - {poet['name']}")
                total_poems_ingested += count
                
                # Add delay to be respectful
                time.sleep(1)
            else:
                print(f"      ❌ Failed to scrape: {poem['title']}")
        
        print(f"   ✅ Scraped {poet_poems_scraped} poems for {poet['name']}")
        
        # Add delay between poets
        time.sleep(2)
    
    print(f"\n🎉 Test Complete!")
    print(f"   📊 Total poems scraped: {total_poems_scraped}")
    print(f"   💾 Total poems ingested: {total_poems_ingested}")
    print(f"   👥 Poets tested: {len(test_poets)}")

def test_single_poem():
    """Test scraping a single poem to verify the scraper works"""
    
    print("🔍 Testing single poem scraping...")
    
    scraper = ItemScraper()
    
    # Test with the Bukowski poem we saw in the search results
    test_url = "https://allpoetry.com/16-bit-Intel-8088-chip"
    
    print(f"📝 Testing: {test_url}")
    poem_data = scraper.scrape_allpoetry_poem(test_url)
    
    if poem_data:
        print("✅ Successfully scraped poem:")
        print(f"   Title: {poem_data['title']}")
        print(f"   Author: {poem_data['author']}")
        print(f"   Text preview: {poem_data['text'][:200]}...")
        print(f"   Source URL: {poem_data['source_url']}")
        
        # Test ingestion
        print("\n💾 Testing ingestion...")
        count = scrape_and_ingest_url(poem_data['source_url'], "AllPoetry Test - Single Poem")
        print(f"✅ Ingested {count} poems")
    else:
        print("❌ Failed to scrape poem")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test AllPoetry scraper")
    parser.add_argument("--single", action="store_true", help="Test single poem scraping")
    parser.add_argument("--poets", action="store_true", help="Test 10 poets scraping")
    
    args = parser.parse_args()
    
    if args.single:
        test_single_poem()
    elif args.poets:
        test_allpoetry_scraper()
    else:
        print("Choose --single or --poets")
        parser.print_help()
