#!/usr/bin/env python3
"""
Clean existing scraped_poems.jsonl to remove analysis and metadata contamination
"""

import json
import re

def clean_poem_text(text):
    """Clean poem text by removing analysis and metadata"""
    if not text:
        return text
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip lines with analysis/metadata
        if any(skip in line.lower() for skip in [
            'show analysis', 
            '© by owner', 
            'composition date', 
            'corrected version', 
            'there is some debate',
            'provided at no charge',
            'from the',
            'this title is not',
            'early editors',
            'the poem with its proper title',
            'we\'ll use the former',
            'some books (and sites) have',
            'whilst others have'
        ]):
            continue
            
        # Skip very short lines
        if len(line) < 3:
            continue
            
        # Skip separator characters
        if line in ['•', '|', '→', '←']:
            continue
            
        # Skip lines that are mostly punctuation
        if len(re.sub(r'[^\w\s]', '', line)) < 3:
            continue
            
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def main():
    """Clean the scraped_poems.jsonl file"""
    
    print("🧹 Starting JSON cleaning process...")
    
    # Read all poems
    poems = []
    with open('scraped_poems.jsonl', 'r') as f:
        for line in f:
            try:
                poem = json.loads(line.strip())
                poems.append(poem)
            except json.JSONDecodeError:
                print(f"⚠️ Skipping malformed JSON line: {line[:50]}...")
                continue
    
    print(f"📖 Loaded {len(poems)} poems")
    
    # Clean each poem
    cleaned_poems = []
    contamination_found = 0
    
    for i, poem in enumerate(poems):
        original_text = poem.get('text', '')
        cleaned_text = clean_poem_text(original_text)
        
        # Check if cleaning removed significant content
        if len(cleaned_text) < 20:
            print(f"⚠️ Poem {i+1} too short after cleaning: {poem.get('title', 'Unknown')}")
            continue
            
        # Check if text was actually cleaned
        if cleaned_text != original_text:
            contamination_found += 1
            removed_lines = len(original_text.split('\n')) - len(cleaned_text.split('\n'))
            print(f"🧹 Cleaned poem {i+1}: {poem.get('title', 'Unknown')} - removed {removed_lines} lines")
        
        # Update the poem with cleaned text
        poem['text'] = cleaned_text
        cleaned_poems.append(poem)
    
    print(f"✅ Cleaned {contamination_found} poems with contamination")
    print(f"📊 Kept {len(cleaned_poems)} poems after cleaning")
    
    # Create backup of original file
    import shutil
    shutil.copy('scraped_poems.jsonl', 'scraped_poems_backup.jsonl')
    print("💾 Created backup: scraped_poems_backup.jsonl")
    
    # Write cleaned poems back to file
    with open('scraped_poems.jsonl', 'w') as f:
        for poem in cleaned_poems:
            f.write(json.dumps(poem) + '\n')
    
    print("✅ Cleaning complete! Original file updated.")
    print(f"📈 Removed {len(poems) - len(cleaned_poems)} contaminated poems")

if __name__ == "__main__":
    main()
