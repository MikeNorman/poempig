#!/usr/bin/env python3
"""
Curation Management Script
Allows you to mark items as user_curated, scraped, or auto_curated
"""

from supabase import create_client
import os
from dotenv import load_dotenv
import json

load_dotenv()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

def get_curation_stats():
    """Get current curation statistics"""
    print("📊 Current Curation Statistics")
    print("=" * 50)
    
    result = sb.table('items').select('curation_type', count='exact').execute()
    
    # Group by curation_type
    stats = {}
    for item in result.data:
        curation_type = item.get('curation_type', 'unknown')
        stats[curation_type] = stats.get(curation_type, 0) + 1
    
    total = sum(stats.values())
    for curation_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"  {curation_type}: {count} items ({percentage:.1f}%)")
    
    print(f"\nTotal items: {total}")
    return stats

def mark_items_as_curated(item_ids, curation_type='user_curated'):
    """Mark specific items as curated"""
    if not item_ids:
        print("❌ No item IDs provided")
        return False
    
    try:
        result = sb.table('items').update({
            'curation_type': curation_type
        }).in_('id', item_ids).execute()
        
        print(f"✅ Marked {len(item_ids)} items as {curation_type}")
        return True
    except Exception as e:
        print(f"❌ Error marking items: {e}")
        return False

def mark_items_by_title_author(title_author_pairs, curation_type='user_curated'):
    """Mark items by title and author pairs"""
    marked_count = 0
    
    for title, author in title_author_pairs:
        try:
            # Find the item
            result = sb.table('items').select('id, title, author').eq('title', title).ilike('author', f'%{author}%').execute()
            
            if result.data:
                item_id = result.data[0]['id']
                sb.table('items').update({'curation_type': curation_type}).eq('id', item_id).execute()
                print(f"✅ Marked: '{title}' by {author}")
                marked_count += 1
            else:
                print(f"❌ Not found: '{title}' by {author}")
        except Exception as e:
            print(f"❌ Error marking '{title}': {e}")
    
    print(f"\n📊 Marked {marked_count} items as {curation_type}")
    return marked_count

def get_curated_items(curation_type='user_curated', limit=10):
    """Get items of a specific curation type"""
    try:
        result = sb.table('items').select('id, title, author, curation_type').eq('curation_type', curation_type).limit(limit).execute()
        
        print(f"📋 {curation_type.title()} Items (showing {len(result.data)} of {result.count}):")
        for item in result.data:
            print(f"  - '{item['title']}' by {item['author']}")
        
        return result.data
    except Exception as e:
        print(f"❌ Error fetching curated items: {e}")
        return []

def search_items_to_curate(query, limit=20):
    """Search for items to potentially curate"""
    try:
        result = sb.table('items').select('id, title, author, curation_type').or_(f'title.ilike.%{query}%,author.ilike.%{query}%').limit(limit).execute()
        
        print(f"🔍 Search Results for '{query}' (showing {len(result.data)}):")
        for item in result.data:
            curation_badge = f"[{item['curation_type']}]" if item.get('curation_type') else "[unknown]"
            print(f"  {curation_badge} '{item['title']}' by {item['author']}")
        
        return result.data
    except Exception as e:
        print(f"❌ Error searching items: {e}")
        return []

def main():
    """Main function with interactive menu"""
    print("🎯 Curation Management Tool")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. View curation statistics")
        print("2. Mark items as user_curated by title/author")
        print("3. Mark items as user_curated by ID")
        print("4. View curated items")
        print("5. Search items to curate")
        print("6. Mark all scraped items as user_curated")
        print("7. Reset all to scraped")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-7): ").strip()
        
        if choice == '0':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            get_curation_stats()
        elif choice == '2':
            print("\nEnter title/author pairs (one per line, format: 'Title' by Author):")
            print("Enter 'done' when finished:")
            pairs = []
            while True:
                line = input("> ").strip()
                if line.lower() == 'done':
                    break
                if ' by ' in line:
                    title, author = line.rsplit(' by ', 1)
                    pairs.append((title.strip(), author.strip()))
                else:
                    print("❌ Format: 'Title' by Author")
            if pairs:
                mark_items_by_title_author(pairs)
        elif choice == '3':
            ids_input = input("Enter item IDs (comma-separated): ").strip()
            if ids_input:
                item_ids = [id.strip() for id in ids_input.split(',')]
                mark_items_as_curated(item_ids)
        elif choice == '4':
            curation_type = input("Enter curation type (user_curated/scraped/auto_curated) [user_curated]: ").strip() or 'user_curated'
            get_curated_items(curation_type)
        elif choice == '5':
            query = input("Enter search query: ").strip()
            if query:
                search_items_to_curate(query)
        elif choice == '6':
            confirm = input("⚠️  Mark ALL scraped items as user_curated? (yes/no): ").strip().lower()
            if confirm == 'yes':
                result = sb.table('items').update({'curation_type': 'user_curated'}).eq('curation_type', 'scraped').execute()
                print(f"✅ Marked {result.count} items as user_curated")
        elif choice == '7':
            confirm = input("⚠️  Reset ALL items to scraped? (yes/no): ").strip().lower()
            if confirm == 'yes':
                result = sb.table('items').update({'curation_type': 'scraped'}).execute()
                print(f"✅ Reset {result.count} items to scraped")
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
