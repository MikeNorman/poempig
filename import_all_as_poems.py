#!/usr/bin/env python3
"""
Import all scraped items as poems (no arbitrary type classification)
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
    raise SystemExit("Missing environment variables")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def import_all_as_poems():
    """Import all scraped items as poems"""
    
    print("📚 Importing all scraped items as poems...")
    
    # Load scraped poems
    poems = []
    with open('scraped_poems.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                poems.append(json.loads(line))
    
    print(f"📖 Loaded {len(poems)} items from scraped_poems.jsonl")
    
    # Check which poems already exist
    existing_urls = set()
    existing_response = sb.table('items').select('source').eq('type', 'poem').execute()
    for item in existing_response.data:
        if item.get('source'):
            existing_urls.add(item['source'])
    
    # Filter out existing poems
    new_poems = []
    for poem in poems:
        if poem.get('source_url') not in existing_urls:
            new_poems.append({
                'title': poem.get('title'),
                'author': poem.get('author'),
                'text': poem.get('text'),
                'year': poem.get('year'),
                'lang': poem.get('lang', 'en'),
                'lines_count': poem.get('lines_count'),
                'tags': poem.get('tags'),
                'type': 'poem',  # All items are poems
                'source': poem.get('source_url'),
                'semantic_tags': poem.get('semantic_tags', [])
            })
    
    print(f"🆕 Found {len(new_poems)} new poems to add")
    print(f"⏭️ Skipping {len(poems) - len(new_poems)} existing poems")
    
    if new_poems:
        # Insert new poems in batches
        batch_size = 100
        for i in range(0, len(new_poems), batch_size):
            batch = new_poems[i:i + batch_size]
            try:
                result = sb.table('items').insert(batch).execute()
                print(f"✅ Inserted batch {i//batch_size + 1}/{(len(new_poems) + batch_size - 1)//batch_size}")
            except Exception as e:
                print(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
    
    return len(new_poems)

def get_final_counts():
    """Get final item counts"""
    
    print("\n📊 Final database counts:")
    
    # Get counts
    poems_count = sb.table('items').select('id', count='exact').eq('type', 'poem').execute()
    quotes_count = sb.table('items').select('id', count='exact').eq('type', 'quote').execute()
    
    print(f"   - Poems: {poems_count.count}")
    print(f"   - Quotes: {quotes_count.count}")
    print(f"   - Total: {poems_count.count + quotes_count.count}")
    
    return poems_count.count + quotes_count.count

def main():
    """Import all scraped items as poems"""
    
    print("🚀 Importing All Scraped Items as Poems")
    print("=" * 50)
    
    # Import poems
    new_poems_count = import_all_as_poems()
    
    # Show final counts
    total_items = get_final_counts()
    
    print(f"\n✅ Import complete!")
    print(f"📈 Added {new_poems_count} new poems")
    print(f"📊 Total items in database: {total_items}")
    
    return total_items

if __name__ == "__main__":
    main()
