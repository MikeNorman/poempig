#!/usr/bin/env python3
"""
Clear and regenerate embeddings properly
"""

import os, backoff
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
from tqdm import tqdm

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 1536

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and OPENAI_API_KEY):
    raise SystemExit("Missing env vars")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
oa = OpenAI(api_key=OPENAI_API_KEY)

@backoff.on_exception(backoff.expo, Exception, max_time=60)
def embed(text: str):
    """Generate embedding for text"""
    return oa.embeddings.create(
        model=EMBEDDING_MODEL, 
        input=text,
        dimensions=EMBEDDING_DIM
    ).data[0].embedding

def main():
    print("🧹 Clearing all existing embeddings...")
    
    # Clear all embeddings (need WHERE clause)
    sb.table('poems').update({'embedding': None}).neq('id', '00000000-0000-0000-0000-000000000000').execute()
    print("✅ Cleared all embeddings")
    
    print("🔍 Getting all items (poems and quotes)...")
    
    # First, check total count in database
    total_count = sb.table('poems').select('id', count='exact').execute()
    print(f"📊 Total items in database: {total_count.count}")
    
    # Get all items using pagination to bypass Supabase's 1000 record limit
    print("🔍 Fetching all items using pagination...")
    all_items = []
    page_size = 1000
    offset = 0
    
    while True:
        print(f"   Fetching page starting at offset {offset}...")
        page = sb.table('poems').select('id, text, author, title, type').range(offset, offset + page_size - 1).execute()
        
        if not page.data:
            break
            
        all_items.extend(page.data)
        print(f"   Got {len(page.data)} items (total so far: {len(all_items)})")
        
        if len(page.data) < page_size:
            break
            
        offset += page_size
    
    if not all_items:
        print("❌ No items found!")
        return
    
    print(f"📝 Total items fetched: {len(all_items)}")
    
    if len(all_items) != total_count.count:
        print(f"⚠️  WARNING: Fetched {len(all_items)} items but database has {total_count.count} total!")
        return
    
    # Count by type
    poem_count = sum(1 for item in all_items if item.get('type') == 'poem')
    quote_count = sum(1 for item in all_items if item.get('type') == 'quote')
    other_count = len(all_items) - poem_count - quote_count
    
    print(f"✅ Item breakdown:")
    print(f"   - Poems: {poem_count}")
    print(f"   - Quotes: {quote_count}")
    print(f"   - Other/Unknown: {other_count}")
    print(f"   - Total: {len(all_items)}")
    
    # Verify we have the right count
    if len(all_items) != 1099:
        print(f"❌ ERROR: Expected 1099 items, got {len(all_items)}. Stopping.")
        return
    
    # Process each item with detailed progress
    successful = 0
    failed = 0
    
    for i, item in enumerate(tqdm(all_items, desc="Generating embeddings", unit="item"), 1):
        try:
            # Show progress every 50 items
            if i % 50 == 0:
                print(f"\n📊 Progress: {i}/{len(all_items)} items processed")
                print(f"✅ Successful: {successful}, ❌ Failed: {failed}")
            
            # Generate embedding
            embedding = embed(item['text'])
            
            # Verify embedding dimensions
            if len(embedding) != EMBEDDING_DIM:
                print(f"\n⚠️  Warning: Item {item['id']} has {len(embedding)} dimensions, expected {EMBEDDING_DIM}")
            
            # Update the item with the embedding
            sb.table('poems').update({
                'embedding': embedding
            }).eq('id', item['id']).execute()
            
            successful += 1
            
        except Exception as e:
            print(f"\n❌ Error processing item {item['id']}: {e}")
            failed += 1
            continue
    
    print("✅ Embedding generation complete!")
    
    # Verify results using pagination
    print("🔍 Verifying embeddings with pagination...")
    poems_with_embeddings = []
    page_size = 1000
    offset = 0
    
    while True:
        page = sb.table('poems').select('id, embedding').not_.is_('embedding', 'null').range(offset, offset + page_size - 1).execute()
        
        if not page.data:
            break
            
        poems_with_embeddings.extend(page.data)
        
        if len(page.data) < page_size:
            break
            
        offset += page_size
    
    print(f"📊 Total items with embeddings: {len(poems_with_embeddings)}")
    
    # Check dimensions of a few samples
    sample = poems_with_embeddings[:3]
    for i, poem in enumerate(sample, 1):
        embedding = poem.get('embedding')
        if embedding:
            print(f"Sample {i}: {len(embedding)} dimensions")

if __name__ == "__main__":
    main()
