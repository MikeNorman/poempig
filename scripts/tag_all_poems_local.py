#!/usr/bin/env python3
"""
Local script to tag all existing poems with semantic tags.
Uses local NLP instead of OpenAI API calls.
"""

import os
import sys
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the parent directory to the path so we can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.local_semantic_tagger import LocalSemanticTagger

load_dotenv()

def main():
    """Tag all poems in the database using local semantic analysis."""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Initialize local semantic tagger
    tagger = LocalSemanticTagger()
    
    print("🏷️  Starting local poem tagging process...")
    
    # Get all items that don't have tags yet
    items_result = supabase.table('items').select('id, title, author, text, type').is_('semantic_tags', 'null').execute()
    
    if not items_result.data:
        print("✅ All items already have tags!")
        return
    
    total_items = len(items_result.data)
    print(f"📚 Found {total_items} items to tag")
    
    # Process items in batches
    batch_size = 50  # Can be larger since no API calls
    processed = 0
    updated = 0
    
    for i in range(0, total_items, batch_size):
        batch = items_result.data[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_items + batch_size - 1) // batch_size
        
        print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
        
        for item in batch:
            try:
                # Analyze item to get tags
                tags = tagger.analyze_poem(
                    item.get('text', ''),
                    item.get('title', ''),
                    item.get('author', '')
                )
                
                # Only process items with real tags
                if tags is None:
                    print(f"  ⚠️  analyze_poem returned None for {item['id']} - skipping")
                    continue
                elif not isinstance(tags, list):
                    print(f"  ⚠️  analyze_poem returned {type(tags)} for {item['id']}: {tags} - skipping")
                    continue
                elif not tags:
                    print(f"  ⚠️  No meaningful tags found for {item['id']} - skipping")
                    continue
                
                # Update item with tags
                supabase.table('items').update({
                    'semantic_tags': tags
                }).eq('id', item['id']).execute()
                
                processed += 1
                updated += 1
                item_type = item.get('type', 'unknown')
                item_title = item.get('title', 'Untitled')
                print(f"  ✓ Tagged {item_type} {processed}/{total_items}: {item_title[:50]}... - {tags}")
                
            except Exception as e:
                print(f"  ❌ Error tagging item {item['id']}: {e}")
                processed += 1
                continue
        
        # Small delay between batches
        if i + batch_size < total_items:
            time.sleep(0.1)  # Very short delay since no API calls
    
    print(f"🎉 Local tagging complete!")
    print(f"   Processed: {processed} items")
    print(f"   Updated: {updated} items")
    print(f"   Success rate: {(updated/processed)*100:.1f}%")

if __name__ == "__main__":
    main()
