#!/usr/bin/env python3
"""
Batched script to tag all existing poems with semantic tags.
Processes 5 items per API call for efficiency.
"""

import os
import sys
import time
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# Add the parent directory to the path so we can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def analyze_poems_batch(poems_batch: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Analyze a batch of poems and extract semantic tags for each.
    
    Args:
        poems_batch: List of poem dictionaries with 'id', 'text', 'title', 'author'
        
    Returns:
        Dict mapping poem_id to list of tags
    """
    try:
        # Create a prompt for batch analysis
        poems_text = ""
        poem_ids = []
        
        for i, poem in enumerate(poems_batch):
            poem_id = poem['id']
            title = poem.get('title', 'Untitled')
            author = poem.get('author', 'Unknown')
            text = poem.get('text', '')
            
            # Skip if text is too short
            if not text or len(text.strip()) < 10:
                continue
                
            poems_text += f"\n--- Poem {i+1} ---\n"
            poems_text += f"ID: {poem_id}\n"
            poems_text += f"Title: {title}\n"
            poems_text += f"Author: {author}\n"
            poems_text += f"Text: {text[:300]}...\n"
            poem_ids.append(poem_id)
        
        if not poem_ids:
            return {}
        
        prompt = f"""
        Analyze these poems and extract 5-10 semantic tags for each one.
        
        {poems_text}
        
        For each poem, return the tags as a comma-separated list. Focus on:
        - Emotional themes (love, grief, joy, melancholy, etc.)
        - Life themes (nature, death, birth, growth, etc.)
        - Literary themes (time, memory, beauty, etc.)
        - Mood/tone (peaceful, intense, contemplative, etc.)
        
        Return the results in this exact JSON format:
        {{
            "poem_id_1": ["tag1", "tag2", "tag3"],
            "poem_id_2": ["tag1", "tag2", "tag3"],
            ...
        }}
        
        If you can't analyze a poem, use: ["unknown", "unclassified"]
        """
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.3
        )
        
        if not response or not response.choices or not response.choices[0].message:
            return {}
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            print(f"Failed to parse JSON response: {result_text[:200]}...")
            return {}
            
    except Exception as e:
        print(f"Error in batch analysis: {e}")
        return {}

def main():
    """Tag all poems in the database using batched processing."""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase: Client = create_client(supabase_url, supabase_key)
    
    print("🏷️  Starting batched poem tagging process...")
    
    # Get all items that don't have tags yet
    items_result = supabase.table('items').select('id, title, author, text, type').is_('semantic_tags', 'null').execute()
    
    if not items_result.data:
        print("✅ All items already have tags!")
        return
    
    total_items = len(items_result.data)
    print(f"📚 Found {total_items} items to tag")
    
    # Process items in batches of 5
    batch_size = 5
    processed = 0
    updated = 0
    
    for i in range(0, total_items, batch_size):
        batch = items_result.data[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_items + batch_size - 1) // batch_size
        
        print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
        
        # Analyze batch
        tags_results = analyze_poems_batch(batch)
        
        if not tags_results:
            print(f"  ❌ Failed to analyze batch {batch_num}")
            processed += len(batch)
            continue
        
        # Update each item with its tags
        for item in batch:
            item_id = item['id']
            processed += 1
            
            if item_id in tags_results:
                tags = tags_results[item_id]
                
                # Ensure tags is a list
                if not isinstance(tags, list):
                    tags = ["unknown", "unclassified"]
                
                # Update item with tags
                try:
                    supabase.table('items').update({
                        'semantic_tags': tags
                    }).eq('id', item_id).execute()
                    
                    updated += 1
                    item_type = item.get('type', 'unknown')
                    item_title = item.get('title', 'Untitled')
                    print(f"  ✓ Tagged {item_type} {processed}/{total_items}: {item_title[:50]}... - {tags}")
                    
                except Exception as e:
                    print(f"  ❌ Error updating item {item_id}: {e}")
            else:
                print(f"  ⚠️  No tags found for item {item_id}")
        
        # Small delay between batches to avoid rate limiting
        if i + batch_size < total_items:
            time.sleep(1)
    
    print(f"🎉 Batched tagging complete!")
    print(f"   Processed: {processed} items")
    print(f"   Updated: {updated} items")
    print(f"   Success rate: {(updated/processed)*100:.1f}%")

if __name__ == "__main__":
    main()
