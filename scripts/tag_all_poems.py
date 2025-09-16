#!/usr/bin/env python3
"""
Script to tag all existing poems with semantic tags.
Run this once to populate the semantic_tags column.
"""

import os
import sys
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from src.semantic_tagger import SemanticTagger

# Add the parent directory to the path so we can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def main():
    """Tag all poems in the database."""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Initialize semantic tagger
    tagger = SemanticTagger()
    
    print("🏷️  Starting poem tagging process...")
    
    # Get all items that don't have tags yet
    items_result = supabase.table('items').select('id, title, author, text, type').is_('semantic_tags', 'null').execute()
    
    if not items_result.data:
        print("✅ All items already have tags!")
        return
    
    total_items = len(items_result.data)
    print(f"📚 Found {total_items} items to tag")
    
    # Process items in batches
    batch_size = 10
    processed = 0
    
    for i in range(0, total_items, batch_size):
        batch = items_result.data[i:i + batch_size]
        
        print(f"🔄 Processing batch {i//batch_size + 1}/{(total_items + batch_size - 1)//batch_size}")
        
        for item in batch:
            try:
                # Analyze item to get tags
                tags = tagger.analyze_poem(
                    item.get('text', ''),
                    item.get('title', ''),  # Use 'title' column
                    item.get('author', '')
                )
                
                # Update item with tags
                supabase.table('items').update({
                    'semantic_tags': tags
                }).eq('id', item['id']).execute()
                
                processed += 1
                item_type = item.get('type', 'unknown')
                item_title = item.get('title', 'Untitled')
                print(f"  ✓ Tagged {item_type} {processed}/{total_items}: {item_title[:50]}... - {tags}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error tagging item {item['id']}: {e}")
                continue
    
    print(f"🎉 Tagging complete! Processed {processed} items.")

if __name__ == "__main__":
    main()
