#!/usr/bin/env python3
"""
Debug version - process just 10 items to see what's happening
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
    """Debug version with extensive logging"""
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Create batch prompt
        batch_text = ""
        for i, item in enumerate(items_batch):
            batch_text += f"\n--- ITEM {i+1} ---\n"
            batch_text += f"ID: {item['id']}\n"
            batch_text += f"Current Title: {item.get('title', 'None')}\n"
            batch_text += f"Current Author: {item.get('author', 'None')}\n"
            batch_text += f"Text: {item['text'][:200]}...\n"
        
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
        - Use exact titles and author names as they're commonly known
        - If uncertain, return null for that field
        - Focus on well-known, classic pieces
        - IMPORTANT: Only identify the MISSING field (title OR author), not both
        """

        print(f"   🔄 Sending request to OpenAI for batch of {len(items_batch)} items...")
        print(f"   📝 Prompt length: {len(prompt)} characters")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,  # Smaller for debug
            temperature=0.1
        )
        print(f"   ✅ OpenAI response received successfully")

        if not response or not response.choices or not response.choices[0].message:
            print(f"   ❌ Empty or invalid response from OpenAI")
            return {}

        result_text = response.choices[0].message.content.strip()
        print(f"   📝 Raw response: {result_text}")
        
        # Try to parse JSON
        try:
            result = json.loads(result_text)
            parsed_result = {item['id']: item for item in result.get('items', [])}
            print(f"   ✅ Successfully parsed {len(parsed_result)} items from response")
            return parsed_result
        except json.JSONDecodeError as e:
            print(f"   ❌ Failed to parse JSON response: {e}")
            print(f"   📝 Raw response was: {result_text}")
            return {}
            
    except Exception as e:
        print(f"   ❌ OpenAI API error: {e}")
        print(f"   🔍 Error type: {type(e).__name__}")
        print(f"   🔍 Error details: {str(e)}")
        return {}

def main():
    """Debug version - process just 10 items"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase: Client = create_client(supabase_url, supabase_key)
    
    print("🔍 Starting DEBUG poem/quote identification process...")
    print("⚡ Processing 10 items only for debugging")
    
    # Get just 10 items that are missing title or author
    items_result = supabase.table('items').select('id, title, author, text, type').or_('title.is.null,author.is.null').limit(10).execute()
    
    if not items_result.data:
        print("✅ All items already have titles and authors!")
        return
    
    total_items = len(items_result.data)
    print(f"📚 Found {total_items} items missing title or author")
    
    # Process items in batches of 2 for debugging
    batch_size = 2
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
        
        # Wait between batches
        if i + batch_size < total_items:
            print(f"   ⏳ Waiting 3 seconds before next batch...")
            time.sleep(3)
    
    print(f"\n🎉 Debug identification complete!")
    print(f"   Processed: {processed} items")
    print(f"   Updated: {updated} items")

if __name__ == "__main__":
    main()
