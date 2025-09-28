#!/usr/bin/env python3
"""
Conservative cleaning of scraped_poems.jsonl - only remove specific contamination patterns
"""

import json
import re

def conservative_clean(text):
    """Very conservative cleaning - only remove specific contamination at the end"""
    if not text:
        return text
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Only remove very specific contamination patterns
        if line in [
            'Show analysis',
            '© by owner. provided at no charge for educational purposes',
            '© by owner. provided at no charge for educational purposes\nShow analysis'
        ]:
            continue
            
        # Remove lines that start with specific patterns
        if line.startswith('Composition date is unknown'):
            continue
            
        # Remove lines that are clearly analysis/metadata
        if (line.startswith('This title is NOT') or 
            line.startswith('Early editors') or
            line.startswith('The poem with its proper title') or
            line.startswith('There is some debate') or
            line.startswith('Some books (and sites) have') or
            line.startswith('whilst others have') or
            line.startswith('We\'ll use the former') or
            line.startswith('From THE ') or
            line.startswith('This poem by ') or
            line.startswith('Charley Noble') or
            line.startswith('http://www.poetryarchive.org') or
            line.startswith('Listen to ') or
            line.startswith('Corrected version from author\'s mss')):
            continue
            
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def main():
    """Conservative cleaning of the JSON file"""
    
    print("🧹 Starting conservative JSON cleaning...")
    
    # Read all poems
    poems = []
    with open('scraped_poems.jsonl', 'r') as f:
        for line in f:
            try:
                poem = json.loads(line.strip())
                poems.append(poem)
            except json.JSONDecodeError:
                print(f"⚠️ Skipping malformed JSON line")
                continue
    
    print(f"📖 Loaded {len(poems)} poems")
    
    # Clean each poem conservatively
    cleaned_poems = []
    contamination_removed = 0
    
    for i, poem in enumerate(poems):
        original_text = poem.get('text', '')
        cleaned_text = conservative_clean(original_text)
        
        # Only keep if we didn't remove too much
        if len(cleaned_text) < 20:
            print(f"⚠️ Poem {i+1} too short after cleaning: {poem.get('title', 'Unknown')}")
            # Keep original if cleaning was too aggressive
            cleaned_text = original_text
        
        # Check if we actually cleaned anything
        if cleaned_text != original_text:
            contamination_removed += 1
            print(f"🧹 Cleaned poem {i+1}: {poem.get('title', 'Unknown')}")
        
        # Update the poem
        poem['text'] = cleaned_text
        cleaned_poems.append(poem)
    
    print(f"✅ Removed contamination from {contamination_removed} poems")
    print(f"📊 Kept {len(cleaned_poems)} poems total")
    
    # Create backup
    import shutil
    shutil.copy('scraped_poems.jsonl', 'scraped_poems_backup.jsonl')
    print("💾 Created backup: scraped_poems_backup.jsonl")
    
    # Write cleaned poems
    with open('scraped_poems.jsonl', 'w') as f:
        for poem in cleaned_poems:
            f.write(json.dumps(poem) + '\n')
    
    print("✅ Conservative cleaning complete!")

if __name__ == "__main__":
    main()
