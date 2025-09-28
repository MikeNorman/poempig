#!/usr/bin/env python3
"""
Data Quality Check for scraped_poems.jsonl
"""

import json
import re
from collections import Counter

def analyze_data_quality():
    """Comprehensive data quality analysis"""
    
    print("🔍 Starting Data Quality Analysis...")
    print("=" * 50)
    
    # Load all poems
    poems = []
    with open('scraped_poems.jsonl', 'r') as f:
        for i, line in enumerate(f):
            try:
                poem = json.loads(line.strip())
                poems.append(poem)
            except json.JSONDecodeError as e:
                print(f"❌ JSON Error on line {i+1}: {e}")
                continue
    
    total_poems = len(poems)
    print(f"📊 Total Poems: {total_poems}")
    print()
    
    # 1. Check for missing fields
    print("1️⃣ MISSING FIELDS CHECK")
    print("-" * 30)
    
    missing_title = sum(1 for p in poems if not p.get('title') or p.get('title') == 'Untitled')
    missing_author = sum(1 for p in poems if not p.get('author') or p.get('author') == 'Unknown')
    missing_text = sum(1 for p in poems if not p.get('text') or len(p.get('text', '').strip()) < 10)
    missing_url = sum(1 for p in poems if not p.get('source_url'))
    
    print(f"Missing/Invalid Titles: {missing_title} ({missing_title/total_poems*100:.1f}%)")
    print(f"Missing/Invalid Authors: {missing_author} ({missing_author/total_poems*100:.1f}%)")
    print(f"Missing/Invalid Text: {missing_text} ({missing_text/total_poems*100:.1f}%)")
    print(f"Missing URLs: {missing_url} ({missing_url/total_poems*100:.1f}%)")
    print()
    
    # 2. Check for contamination in text field
    print("2️⃣ TEXT CONTAMINATION CHECK")
    print("-" * 30)
    
    contamination_patterns = [
        'Show analysis',
        '© by owner',
        'Composition date',
        'Corrected version',
        'There is some debate',
        'provided at no charge',
        'From THE ',
        'This poem by ',
        'Charley Noble',
        'http://www.poetryarchive.org',
        'Listen to '
    ]
    
    contaminated_poems = 0
    for pattern in contamination_patterns:
        count = sum(1 for p in poems if pattern in p.get('text', ''))
        if count > 0:
            print(f"'{pattern}': {count} poems")
            contaminated_poems += count
    
    print(f"Total contaminated poems: {contaminated_poems}")
    print()
    
    # 3. Check for duplicate URLs
    print("3️⃣ DUPLICATE CHECK")
    print("-" * 30)
    
    urls = [p.get('source_url') for p in poems if p.get('source_url')]
    url_counts = Counter(urls)
    duplicates = sum(1 for count in url_counts.values() if count > 1)
    duplicate_urls = [url for url, count in url_counts.items() if count > 1]
    
    print(f"Duplicate URLs: {duplicates}")
    if duplicate_urls:
        print(f"Example duplicates: {duplicate_urls[:3]}")
    print()
    
    # 4. Check text length distribution
    print("4️⃣ TEXT LENGTH ANALYSIS")
    print("-" * 30)
    
    text_lengths = [len(p.get('text', '')) for p in poems]
    avg_length = sum(text_lengths) / len(text_lengths)
    min_length = min(text_lengths)
    max_length = max(text_lengths)
    
    # Count by length ranges
    very_short = sum(1 for l in text_lengths if l < 50)
    short = sum(1 for l in text_lengths if 50 <= l < 200)
    medium = sum(1 for l in text_lengths if 200 <= l < 1000)
    long = sum(1 for l in text_lengths if l >= 1000)
    
    print(f"Average text length: {avg_length:.0f} characters")
    print(f"Min length: {min_length} characters")
    print(f"Max length: {max_length} characters")
    print(f"Very short (<50 chars): {very_short} ({very_short/total_poems*100:.1f}%)")
    print(f"Short (50-199 chars): {short} ({short/total_poems*100:.1f}%)")
    print(f"Medium (200-999 chars): {medium} ({medium/total_poems*100:.1f}%)")
    print(f"Long (1000+ chars): {long} ({long/total_poems*100:.1f}%)")
    print()
    
    # 5. Check author distribution
    print("5️⃣ AUTHOR DISTRIBUTION")
    print("-" * 30)
    
    authors = [p.get('author') for p in poems if p.get('author')]
    author_counts = Counter(authors)
    top_authors = author_counts.most_common(10)
    
    print("Top 10 authors by poem count:")
    for author, count in top_authors:
        print(f"  {author}: {count} poems")
    print()
    
    # 6. Check for empty or malformed data
    print("6️⃣ MALFORMED DATA CHECK")
    print("-" * 30)
    
    empty_poems = sum(1 for p in poems if not p.get('text') or len(p.get('text', '').strip()) < 5)
    malformed_json = 0  # We already caught these above
    
    print(f"Empty/Invalid poems: {empty_poems}")
    print(f"Malformed JSON: {malformed_json}")
    print()
    
    # 7. Sample quality check
    print("7️⃣ SAMPLE QUALITY CHECK")
    print("-" * 30)
    
    print("Sample poems (first 3):")
    for i, poem in enumerate(poems[:3]):
        print(f"\nPoem {i+1}:")
        print(f"  Title: {poem.get('title', 'N/A')}")
        print(f"  Author: {poem.get('author', 'N/A')}")
        print(f"  Text length: {len(poem.get('text', ''))} chars")
        print(f"  Text preview: {poem.get('text', '')[:100]}...")
        print(f"  URL: {poem.get('source_url', 'N/A')}")
    
    # 8. Overall quality score
    print("\n8️⃣ OVERALL QUALITY SCORE")
    print("-" * 30)
    
    quality_issues = 0
    quality_issues += missing_title
    quality_issues += missing_author  
    quality_issues += missing_text
    quality_issues += missing_url
    quality_issues += contaminated_poems
    quality_issues += duplicates
    quality_issues += empty_poems
    
    quality_score = max(0, 100 - (quality_issues / total_poems * 100))
    
    print(f"Quality Score: {quality_score:.1f}/100")
    print(f"Total Issues: {quality_issues}")
    print(f"Issue Rate: {quality_issues/total_poems*100:.1f}%")
    
    if quality_score >= 90:
        print("✅ EXCELLENT quality - ready for ingestion!")
    elif quality_score >= 80:
        print("⚠️ GOOD quality - minor cleaning recommended")
    elif quality_score >= 70:
        print("⚠️ FAIR quality - cleaning recommended")
    else:
        print("❌ POOR quality - significant cleaning required")

if __name__ == "__main__":
    analyze_data_quality()
