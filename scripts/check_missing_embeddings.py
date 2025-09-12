#!/usr/bin/env python3
"""
Check which items in the database are missing embeddings
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
    raise SystemExit("Missing Supabase environment variables")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def check_missing_embeddings():
    """Check which items are missing embeddings"""
    print("🔍 Checking for items missing embeddings...")
    
    # Get total count
    total_count = sb.table('poems').select('id', count='exact').execute()
    print(f"📊 Total items in database: {total_count.count}")
    
    # Get items with embeddings
    items_with_embeddings = []
    page_size = 1000
    offset = 0
    
    while True:
        print(f"   Checking page starting at offset {offset}...")
        page = sb.table('poems').select('id, title, author, type, embedding').not_.is_('embedding', 'null').range(offset, offset + page_size - 1).execute()
        
        if not page.data:
            break
            
        items_with_embeddings.extend(page.data)
        print(f"   Found {len(page.data)} items with embeddings (total so far: {len(items_with_embeddings)})")
        
        if len(page.data) < page_size:
            break
            
        offset += page_size
    
    # Get items without embeddings
    items_without_embeddings = []
    offset = 0
    
    while True:
        print(f"   Checking for items without embeddings at offset {offset}...")
        page = sb.table('poems').select('id, title, author, type, embedding').is_('embedding', 'null').range(offset, offset + page_size - 1).execute()
        
        if not page.data:
            break
            
        items_without_embeddings.extend(page.data)
        print(f"   Found {len(page.data)} items without embeddings (total so far: {len(items_without_embeddings)})")
        
        if len(page.data) < page_size:
            break
            
        offset += page_size
    
    print(f"\n📊 Summary:")
    print(f"   - Total items: {total_count.count}")
    print(f"   - Items with embeddings: {len(items_without_embeddings)}")
    print(f"   - Items without embeddings: {len(items_without_embeddings)}")
    
    if items_without_embeddings:
        print(f"\n❌ Found {len(items_without_embeddings)} items missing embeddings:")
        
        # Show breakdown by type
        poem_count = sum(1 for item in items_without_embeddings if item.get('type') == 'poem')
        quote_count = sum(1 for item in items_without_embeddings if item.get('type') == 'quote')
        other_count = len(items_without_embeddings) - poem_count - quote_count
        
        print(f"   - Poems: {poem_count}")
        print(f"   - Quotes: {quote_count}")
        print(f"   - Other/Unknown: {other_count}")
        
        # Show first few examples
        print(f"\n📝 First 10 items missing embeddings:")
        for i, item in enumerate(items_without_embeddings[:10], 1):
            print(f"   {i}. {item.get('title', 'No title')} by {item.get('author', 'Unknown')} ({item.get('type', 'unknown')})")
        
        if len(items_without_embeddings) > 10:
            print(f"   ... and {len(items_without_embeddings) - 10} more")
        
        return items_without_embeddings
    else:
        print(f"\n✅ All items have embeddings!")
        return []

if __name__ == "__main__":
    missing_items = check_missing_embeddings()
    
    if missing_items:
        print(f"\n🔧 Run the following command to generate missing embeddings:")
        print(f"   python scripts/generate_missing_embeddings.py")
    else:
        print(f"\n🎉 No action needed - all items have embeddings!")
