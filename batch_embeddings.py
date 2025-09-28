#!/usr/bin/env python3
"""
Batch embedding generation with progress tracking and resumption
"""

import os
import json
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
from tqdm import tqdm

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"  # Use smaller model for speed
EMBEDDING_DIM = 1536

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and OPENAI_API_KEY):
    raise SystemExit("Missing env vars")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
oa = OpenAI(api_key=OPENAI_API_KEY)

def embed_text(text: str):
    """Generate embedding for text"""
    try:
        return oa.embeddings.create(
            model=EMBEDDING_MODEL, 
            input=text,
            dimensions=EMBEDDING_DIM
        ).data[0].embedding
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return None

def get_items_without_embeddings():
    """Get all items without embeddings using pagination"""
    items = []
    offset = 0
    limit = 1000
    
    while True:
        batch = sb.table('items').select('id, text, author, title, type').is_('embedding', 'null').range(offset, offset + limit - 1).execute()
        if not batch.data:
            break
        items.extend(batch.data)
        offset += limit
        print(f"Found {len(items)} items without embeddings...")
    
    return items

def process_batch(items, batch_size=50):
    """Process items in batches"""
    total_processed = 0
    total_errors = 0
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        print(f"\n🔄 Processing batch {i//batch_size + 1}/{(len(items) + batch_size - 1)//batch_size}")
        
        for item in tqdm(batch, desc=f"Batch {i//batch_size + 1}"):
            try:
                embedding = embed_text(item['text'])
                if embedding:
                    sb.table('items').update({
                        'embedding': embedding
                    }).eq('id', item['id']).execute()
                    total_processed += 1
                else:
                    total_errors += 1
            except Exception as e:
                print(f"❌ Error processing {item['id']}: {e}")
                total_errors += 1
        
        # Small delay between batches to avoid rate limits
        time.sleep(1)
        
        # Show progress
        remaining = len(items) - (i + len(batch))
        print(f"✅ Processed {total_processed} items, {total_errors} errors, {remaining} remaining")
    
    return total_processed, total_errors

def main():
    print("🚀 Starting Batch Embedding Generation")
    print("=" * 50)
    
    # Get items without embeddings
    print("🔍 Finding items without embeddings...")
    items = get_items_without_embeddings()
    
    if not items:
        print("✅ All items already have embeddings!")
        return
    
    print(f"📝 Found {len(items)} items without embeddings")
    
    # Process in batches
    processed, errors = process_batch(items, batch_size=50)
    
    print(f"\n✅ Batch processing complete!")
    print(f"📊 Processed: {processed}")
    print(f"❌ Errors: {errors}")
    
    # Final verification
    remaining = sb.table('items').select('id', count='exact').is_('embedding', 'null').execute()
    print(f"📈 Remaining without embeddings: {remaining.count}")

if __name__ == "__main__":
    main()
