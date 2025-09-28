#!/usr/bin/env python3
"""
Generate embeddings for existing poems in the database
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
    print("🔍 Finding poems without embeddings...")
    
    # Get all items that don't have embeddings (with pagination to get all)
    items_without_embeddings = []
    offset = 0
    limit = 1000
    
    while True:
        batch = sb.table('items').select('id, text, author, title, type').is_('embedding', 'null').range(offset, offset + limit - 1).execute()
        if not batch.data:
            break
        items_without_embeddings.extend(batch.data)
        offset += limit
        print(f"Found {len(items_without_embeddings)} items without embeddings so far...")
    
    if not items_without_embeddings:
        print("✅ All items already have embeddings!")
        return
    
    print(f"📝 Found {len(items_without_embeddings)} items without embeddings")
    
    # Process each item
    for item in tqdm(items_without_embeddings, desc="Generating embeddings"):
        try:
            # Generate embedding
            embedding = embed(item['text'])
            
            # Ensure embedding is a proper list/array
            if isinstance(embedding, str):
                # If it's a string, try to parse it
                import json
                embedding = json.loads(embedding)
            
            # Update the item with the embedding
            sb.table('items').update({
                'embedding': embedding
            }).eq('id', item['id']).execute()
            
        except Exception as e:
            print(f"❌ Error processing item {item['id']} ({item.get('type', 'unknown')}): {e}")
            continue
    
    print("✅ Embedding generation complete!")
    
    # Verify results
    items_with_embeddings = sb.table('items').select('id', count='exact').not_.is_('embedding', 'null').execute()
    print(f"📊 Total items with embeddings: {items_with_embeddings.count}")

if __name__ == "__main__":
    main()
