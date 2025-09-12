#!/usr/bin/env python3
"""
Generate embeddings for items that are missing them
"""

import os
import backoff
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
from tqdm import tqdm

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = 1536 if "large" in EMBEDDING_MODEL else 384

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and OPENAI_API_KEY):
    raise SystemExit("Missing environment variables")

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

def get_items_without_embeddings():
    """Get all items that are missing embeddings"""
    print("🔍 Finding items without embeddings...")
    
    items_without_embeddings = []
    page_size = 1000
    offset = 0
    
    while True:
        print(f"   Checking page starting at offset {offset}...")
        page = sb.table('poems').select('id, title, author, type, text, embedding').is_('embedding', 'null').range(offset, offset + page_size - 1).execute()
        
        if not page.data:
            break
            
        items_without_embeddings.extend(page.data)
        print(f"   Found {len(page.data)} items without embeddings (total so far: {len(items_without_embeddings)})")
        
        if len(page.data) < page_size:
            break
            
        offset += page_size
    
    return items_without_embeddings

def generate_missing_embeddings():
    """Generate embeddings for all items that are missing them"""
    # Get items without embeddings
    items_without_embeddings = get_items_without_embeddings()
    
    if not items_without_embeddings:
        print("✅ No items missing embeddings!")
        return
    
    print(f"\n📝 Found {len(items_without_embeddings)} items missing embeddings")
    
    # Show breakdown by type
    poem_count = sum(1 for item in items_without_embeddings if item.get('type') == 'poem')
    quote_count = sum(1 for item in items_without_embeddings if item.get('type') == 'quote')
    other_count = len(items_without_embeddings) - poem_count - quote_count
    
    print(f"   - Poems: {poem_count}")
    print(f"   - Quotes: {quote_count}")
    print(f"   - Other/Unknown: {other_count}")
    
    # Process each item
    successful = 0
    failed = 0
    
    print(f"\n🔄 Generating embeddings...")
    
    for item in tqdm(items_without_embeddings, desc="Generating embeddings", unit="item"):
        try:
            # Get the text to embed
            text = item.get('text', '')
            if not text:
                print(f"\n⚠️  Warning: Item {item['id']} has no text, skipping")
                failed += 1
                continue
            
            # Generate embedding
            embedding = embed(text)
            
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
    
    print(f"\n📊 Results:")
    print(f"   - Successful: {successful}")
    print(f"   - Failed: {failed}")
    print(f"   - Total processed: {successful + failed}")
    
    if successful > 0:
        print(f"\n✅ Successfully generated {successful} embeddings!")
    
    if failed > 0:
        print(f"\n❌ Failed to generate {failed} embeddings. Check the errors above.")

def verify_all_embeddings():
    """Verify that all items now have embeddings"""
    print(f"\n🔍 Verifying all items have embeddings...")
    
    # Count items with embeddings
    items_with_embeddings = []
    page_size = 1000
    offset = 0
    
    while True:
        page = sb.table('poems').select('id, embedding').not_.is_('embedding', 'null').range(offset, offset + page_size - 1).execute()
        
        if not page.data:
            break
            
        items_with_embeddings.extend(page.data)
        
        if len(page.data) < page_size:
            break
            
        offset += page_size
    
    # Count total items
    total_count = sb.table('poems').select('id', count='exact').execute()
    
    print(f"📊 Verification results:")
    print(f"   - Total items: {total_count.count}")
    print(f"   - Items with embeddings: {len(items_with_embeddings)}")
    print(f"   - Items without embeddings: {total_count.count - len(items_with_embeddings)}")
    
    if len(items_with_embeddings) == total_count.count:
        print(f"✅ All items now have embeddings!")
        return True
    else:
        print(f"❌ Some items still missing embeddings!")
        return False

if __name__ == "__main__":
    print("🚀 Starting missing embeddings generation...")
    
    # Generate missing embeddings
    generate_missing_embeddings()
    
    # Verify all items have embeddings
    verify_all_embeddings()
    
    print(f"\n🎉 Done!")
