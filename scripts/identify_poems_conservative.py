#!/usr/bin/env python3
"""
Conservative script to identify and populate missing titles and authors.
Only updates when GPT is very confident (high confidence only).
"""

import os
import sys
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# Add the parent directory to the path so we can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def identify_poem_conservative(text):
    """
    Use GPT to identify a poem/quote with very high confidence requirement.
    
    Returns:
        dict: {'title': str, 'author': str, 'confidence': str, 'reasoning': str}
    """
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""
        Identify this well-known poem or quote. Be VERY conservative - only identify if you're 100% certain.
        
        Return ONLY a JSON object with this exact structure:
        {{
            "title": "exact title or null if uncertain",
            "author": "exact author name or null if uncertain", 
            "confidence": "high/medium/low",
            "reasoning": "brief explanation"
        }}

        Text to identify:
        {text[:500]}

        IMPORTANT RULES:
        - Only return "high" confidence if you're 100% certain this is a famous, well-known piece
        - Only identify if it's a classic poem, famous quote, or widely recognized literary work
        - If you have ANY doubt, return null for that field
        - Use exact titles and author names as they're commonly known
        - Focus on pieces that would be in a standard literature curriculum
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.0  # Very low temperature for consistency
        )

        if not response or not response.choices or not response.choices[0].message:
            return None

        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            return {
                "title": None,
                "author": None, 
                "confidence": "low",
                "reasoning": "Failed to parse response"
            }

    except Exception as e:
        print(f"Error identifying poem: {e}")
        return None

def main():
    """Identify and update missing titles/authors for items (conservative approach)."""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase: Client = create_client(supabase_url, supabase_key)
    
    print("🔍 Starting CONSERVATIVE poem/quote identification process...")
    print("⚠️  Only updating items with HIGH confidence identifications")
    
    # Get items that are missing title or author
    items_result = supabase.table('items').select('id, title, author, text, type').or_('title.is.null,author.is.null').execute()
    
    if not items_result.data:
        print("✅ All items already have titles and authors!")
        return
    
    total_items = len(items_result.data)
    print(f"📚 Found {total_items} items missing title or author")
    
    # Process items
    processed = 0
    updated = 0
    high_confidence = 0
    
    for item in items_result.data:
        try:
            current_title = item.get('title')
            current_author = item.get('author')
            text = item.get('text', '')
            
            # Skip if text is too short
            if len(text.strip()) < 20:
                print(f"  ⏭️  Skipping {item['id']}: text too short")
                continue
            
            print(f"\n🔍 Analyzing item {processed + 1}/{total_items}:")
            print(f"   Current: title='{current_title}', author='{current_author}'")
            print(f"   Text: {text[:100]}...")
            
            # Identify the piece
            identification = identify_poem_conservative(text)
            
            if not identification:
                print(f"   ❌ Failed to identify")
                processed += 1
                continue
            
            print(f"   🤖 GPT Result: {identification}")
            
            # Only update if confidence is HIGH
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
                    supabase.table('items').update(update_data).eq('id', item['id']).execute()
                    updated += 1
                    print(f"   🎉 Updated item {item['id']}")
                else:
                    print(f"   ⏭️  No updates needed")
            else:
                print(f"   ⏭️  Confidence too low ({identification['confidence']}) - skipping")
            
            processed += 1
            
            # Rate limiting
            time.sleep(1.5)  # Slower to be more careful
            
        except Exception as e:
            print(f"   ❌ Error processing item {item['id']}: {e}")
            processed += 1
            continue
    
    print(f"\n🎉 Conservative identification complete!")
    print(f"   Processed: {processed} items")
    print(f"   High confidence: {high_confidence} items")
    print(f"   Updated: {updated} items")

if __name__ == "__main__":
    main()
