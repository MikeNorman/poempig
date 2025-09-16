#!/usr/bin/env python3
"""
Batched script to identify and populate missing titles and authors.
Processes 5 items at once with 95% certainty requirement.
"""

import os
import sys
import time
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# Add the parent directory to the path so we can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def identify_poems_batch(items_batch):
    """
    Use GPT to identify multiple poems/quotes in one API call.
    
    Args:
        items_batch: List of items with id, text, current title, current author
    
    Returns:
        dict: Mapping of item_id to identification results
    """
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Create batch prompt
        batch_text = ""
        for i, item in enumerate(items_batch):
            batch_text += f"\n--- ITEM {i+1} ---\n"
            batch_text += f"ID: {item['id']}\n"
            batch_text += f"Current Title: {item.get('title', 'None')}\n"
            batch_text += f"Current Author: {item.get('author', 'None')}\n"
            batch_text += f"Text: {item['text'][:300]}...\n"
        
        prompt = f"""
        Identify these poems/quotes. Be 95% confident - only identify if you're very certain.
        
        Return ONLY a JSON object with this exact structure:
        {{
            "items": [
                {{
                    "id": "item_id",
                    "title": "exact title or null if uncertain",
                    "author": "exact author name or null if uncertain", 
                    "confidence": "high/medium/low",
                    "reasoning": "brief explanation"
                }}
            ]
        }}

        Items to identify:
        {batch_text}

        RULES:
        - Only return "high" confidence if you're 95%+ certain
        - Only return "medium" if you're 80%+ certain  
        - Return "low" for anything less certain
        - Use exact titles and author names as they're commonly known
        - If uncertain, return null for that field
        - Focus on well-known, classic pieces
        - IMPORTANT: Only identify the MISSING field (title OR author), not both
        - If an item already has an author, focus on identifying the title
        - If an item already has a title, focus on identifying the author
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,  # More tokens for batch processing
            temperature=0.1
        )

        if not response or not response.choices or not response.choices[0].message:
            return {}

        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON
        try:
            result = json.loads(result_text)
            # Convert to dict keyed by item_id for easy lookup
            return {item['id']: item for item in result.get('items', [])}
        except json.JSONDecodeError:
            print(f"Failed to parse JSON response: {result_text}")
            return {}

    except Exception as e:
        print(f"Error identifying poems batch: {e}")
        return {}

def main():
    """Identify and update missing titles/authors for items (batched approach)."""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase: Client = create_client(supabase_url, supabase_key)
    
    print("🔍 Starting BATCHED poem/quote identification process...")
    print("⚡ Processing 5 items at once with 95% certainty requirement")
    
    # Get ALL items that are missing title OR author
    items_result = supabase.table('items').select('id, title, author, text, type').or_('title.is.null,author.is.null').execute()
    
    if not items_result.data:
        print("✅ All items already have titles and authors!")
        return
    
    total_items = len(items_result.data)
    print(f"📚 Found {total_items} items missing title or author")
    
    # Process items in batches of 5
    batch_size = 5
    processed = 0
    updated = 0
    high_confidence = 0
    
    for i in range(0, total_items, batch_size):
        batch = items_result.data[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_items + batch_size - 1) // batch_size
        
        print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
        
        # Filter out items with very short text
        valid_batch = [item for item in batch if len(item.get('text', '').strip()) >= 20]
        
        if not valid_batch:
            print(f"   ⏭️  Skipping batch: all items too short")
            processed += len(batch)
            continue
        
        print(f"   📝 Analyzing {len(valid_batch)} items...")
        
        # Identify the batch
        identifications = identify_poems_batch(valid_batch)
        
        if not identifications:
            print(f"   ❌ Failed to identify batch")
            processed += len(batch)
            continue
        
        # Process each item in the batch
        for item in valid_batch:
            item_id = item['id']
            current_title = item.get('title')
            current_author = item.get('author')
            
            if item_id not in identifications:
                print(f"   ⚠️  No identification for {item_id}")
                continue
            
            identification = identifications[item_id]
            print(f"   🤖 {item_id}: {identification}")
            
            # Update ONLY if confidence is high (95%+)
            if identification['confidence'] == 'high':
                high_confidence += 1
                
                update_data = {}
                
                if not current_title and identification['title']:
                    update_data['title'] = identification['title']
                    print(f"   ✅ Will update title: {identification['title']}")
                
                if not current_author and identification['author']:
                    update_data['author'] = identification['author']
                    print(f"   ✅ Will update author: {identification['author']}")
                
                if update_data:
                    # Update the item
                    supabase.table('items').update(update_data).eq('id', item_id).execute()
                    updated += 1
                    print(f"   🎉 Updated item {item_id}")
                else:
                    print(f"   ⏭️  No updates needed for {item_id}")
            else:
                print(f"   ⏭️  Confidence too low ({identification['confidence']}) for {item_id} - skipping")
        
        processed += len(batch)
        
        # Rate limiting - shorter delay since we're batching
        if i + batch_size < total_items:  # Don't delay after last batch
            time.sleep(2)  # 2 seconds between batches
    
    print(f"\n🎉 Batched identification complete!")
    print(f"   Processed: {processed} items")
    print(f"   High confidence: {high_confidence} items")
    print(f"   Updated: {updated} items")
    print(f"   Success rate: {(updated/processed)*100:.1f}%")

if __name__ == "__main__":
    main()
