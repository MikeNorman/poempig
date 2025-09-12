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
    
    # Get all poems that don't have embeddings
    poems_without_embeddings = sb.table('poems').select('id, text, author, title').is_('embedding', 'null').execute()
    
    if not poems_without_embeddings.data:
        print("✅ All poems already have embeddings!")
        return
    
    print(f"📝 Found {len(poems_without_embeddings.data)} poems without embeddings")
    
    # Process each poem
    for poem in tqdm(poems_without_embeddings.data, desc="Generating embeddings"):
        try:
            # Generate embedding
            embedding = embed(poem['text'])
            
            # Ensure embedding is a proper list/array
            if isinstance(embedding, str):
                # If it's a string, try to parse it
                import json
                embedding = json.loads(embedding)
            
            # Update the poem with the embedding
            sb.table('poems').update({
                'embedding': embedding
            }).eq('id', poem['id']).execute()
            
        except Exception as e:
            print(f"❌ Error processing poem {poem['id']}: {e}")
            continue
    
    print("✅ Embedding generation complete!")
    
    # Verify results
    poems_with_embeddings = sb.table('poems').select('id').not_.is_('embedding', 'null').execute()
    print(f"📊 Total poems with embeddings: {len(poems_with_embeddings.data)}")

if __name__ == "__main__":
    main()
