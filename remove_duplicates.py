#!/usr/bin/env python3
"""
Remove true duplicates from scraped_poems.jsonl
"""

import json
from collections import defaultdict

def remove_duplicates():
    """Remove duplicate poems based on source_url"""
    
    print("🔍 Removing duplicate poems...")
    
    # Load all poems
    poems = []
    with open('scraped_poems.jsonl', 'r') as f:
        for line in f:
            try:
                poem = json.loads(line.strip())
                poems.append(poem)
            except json.JSONDecodeError:
                continue
    
    print(f"📖 Loaded {len(poems)} poems")
    
    # Group by URL to find duplicates
    url_groups = defaultdict(list)
    for i, poem in enumerate(poems):
        url = poem.get('source_url')
        if url:
            url_groups[url].append((i, poem))
    
    # Find duplicates
    duplicates = {url: poems for url, poems in url_groups.items() if len(poems) > 1}
    
    print(f"🔍 Found {len(duplicates)} URLs with duplicates")
    
    # Keep only the first occurrence of each URL
    seen_urls = set()
    unique_poems = []
    removed_count = 0
    
    for poem in poems:
        url = poem.get('source_url')
        if url not in seen_urls:
            seen_urls.add(url)
            unique_poems.append(poem)
        else:
            removed_count += 1
    
    print(f"✅ Removed {removed_count} duplicate poems")
    print(f"📊 Kept {len(unique_poems)} unique poems")
    
    # Create backup
    import shutil
    shutil.copy('scraped_poems.jsonl', 'scraped_poems_with_duplicates.jsonl')
    print("💾 Created backup: scraped_poems_with_duplicates.jsonl")
    
    # Write unique poems
    with open('scraped_poems.jsonl', 'w') as f:
        for poem in unique_poems:
            f.write(json.dumps(poem) + '\n')
    
    print("✅ Duplicate removal complete!")

if __name__ == "__main__":
    remove_duplicates()
