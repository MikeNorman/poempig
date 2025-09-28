#!/usr/bin/env python3
"""
Add new scraped poems and regenerate embeddings for ALL items
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

def add_scraped_poems():
    """Add new scraped poems to the database"""
    
    print("📚 Adding scraped poems to database...")
    
    # Load scraped poems
    poems = []
    with open('scraped_poems.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                poems.append(json.loads(line))
    
    print(f"📖 Loaded {len(poems)} poems from scraped_poems.jsonl")
    
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
                'type': 'poem',
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

def get_all_items():
    """Get all items that need embeddings"""
    
    print("🔍 Getting all items for embedding generation...")
    
    # Get all items
    response = sb.table('items').select('id,title,author,text,type').execute()
    items = response.data
    
    print(f"📊 Found {len(items)} total items")
    
    # Count by type
    poems = [item for item in items if item.get('type') == 'poem']
    quotes = [item for item in items if item.get('type') == 'quote']
    
    print(f"   - Poems: {len(poems)}")
    print(f"   - Quotes: {len(quotes)}")
    
    return items

def main():
    """Add poems and regenerate all embeddings"""
    
    print("🚀 Adding Poems and Regenerating All Embeddings")
    print("=" * 50)
    
    # Step 1: Add scraped poems
    print("\n1️⃣ Adding scraped poems...")
    new_poems_count = add_scraped_poems()
    
    # Step 2: Get all items for embedding generation
    print("\n2️⃣ Preparing for embedding generation...")
    all_items = get_all_items()
    
    print(f"\n✅ Ready to regenerate embeddings for {len(all_items)} items")
    print(f"📈 Added {new_poems_count} new poems")
    
    print("\nNext step:")
    print("Run: python scripts/generate_embeddings.py")
    
    return len(all_items)

if __name__ == "__main__":
    main()
