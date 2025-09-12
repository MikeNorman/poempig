#!/usr/bin/env python3
"""
Test average coherence between items grouped by author (for non-null authors)
"""

import os
import sys
import numpy as np
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm

# Add src to path
sys.path.append('src')
from recommendation_engine import PoemRecommendationEngine

load_dotenv()

def embedding_coherence(X):
    """
    X: np.ndarray of shape (n, d). L2-normalize first (rows sum of squares = 1).
    Returns mean pairwise cosine, min pairwise cosine, centroid tightness, and LOO drift (deg).
    """
    # L2 normalize rows
    X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
    
    # pairwise cosines
    sims = X @ X.T
    iu = np.triu_indices(len(X), 1)
    mpc = float(sims[iu].mean()) if len(iu[0]) else 1.0
    min_cos = float(sims[iu].min()) if len(iu[0]) else 1.0
    
    # centroid tightness
    c = X.mean(0)
    c /= (np.linalg.norm(c) + 1e-12)
    ct = float((X @ c).mean())
    
    # leave-one-out centroid drift (in degrees)
    if len(X) > 2:
        drifts = []
        sumX = X.sum(0)
        for i in range(len(X)):
            ci = (sumX - X[i]) / (len(X)-1)
            ci /= (np.linalg.norm(ci) + 1e-12)
            drifts.append(np.degrees(np.arccos(np.clip(c @ ci, -1, 1))))
        loo_deg = float(max(drifts))
    else:
        loo_deg = 0.0
    
    return {
        "mean_pairwise": mpc, 
        "min_pairwise": min_cos, 
        "centroid_tightness": ct, 
        "loo_drift_deg": loo_deg
    }

def get_all_embeddings():
    """Get all embeddings from the database"""
    print("🔍 Retrieving all embeddings from database...")
    
    engine = PoemRecommendationEngine()
    all_poems = engine.get_poem_embeddings()
    
    print(f"📊 Retrieved {len(all_poems)} poems")
    
    # Extract embeddings
    embeddings = []
    valid_poems = []
    
    for poem in all_poems:
        embedding = poem.get('embedding')
        if embedding is not None:
            # Convert to numpy array if it's a string
            if isinstance(embedding, str):
                try:
                    embedding = json.loads(embedding)
                except:
                    continue
            elif isinstance(embedding, list):
                pass  # Already a list
            else:
                continue
                
            embeddings.append(embedding)
            valid_poems.append(poem)
    
    print(f"✅ Found {len(embeddings)} valid embeddings")
    return np.array(embeddings), valid_poems

def analyze_author_coherence(embeddings, poems, min_items=2):
    """Analyze coherence for all authors with at least min_items"""
    print(f"\n📊 Analyzing coherence for all authors (min {min_items} items)...")
    
    # Group by author (excluding null/empty authors)
    author_groups = {}
    for i, poem in enumerate(poems):
        author = poem.get('author', '').strip()
        if author and author.lower() not in ['unknown', 'null', 'none', '']:
            if author not in author_groups:
                author_groups[author] = []
            author_groups[author].append(i)
    
    print(f"📝 Found {len(author_groups)} authors with non-null names")
    
    # Filter authors with enough items
    valid_authors = {author: indices for author, indices in author_groups.items() if len(indices) >= min_items}
    print(f"📝 {len(valid_authors)} authors have at least {min_items} items")
    
    # Calculate coherence for each author
    author_coherences = {}
    
    for author, indices in tqdm(valid_authors.items(), desc="Analyzing authors"):
        author_embeddings = embeddings[indices]
        
        if len(author_embeddings) >= 2:  # Need at least 2 for coherence
            coherence = embedding_coherence(author_embeddings)
            author_coherences[author] = {
                'coherence': coherence,
                'count': len(indices)
            }
    
    return author_coherences

def calculate_average_coherence(author_coherences):
    """Calculate average coherence across all authors"""
    print(f"\n📊 Calculating average coherence across {len(author_coherences)} authors...")
    
    if not author_coherences:
        print("❌ No authors found!")
        return None
    
    # Extract metrics
    mean_pairwise_values = [data['coherence']['mean_pairwise'] for data in author_coherences.values()]
    min_pairwise_values = [data['coherence']['min_pairwise'] for data in author_coherences.values()]
    centroid_tightness_values = [data['coherence']['centroid_tightness'] for data in author_coherences.values()]
    loo_drift_values = [data['coherence']['loo_drift_deg'] for data in author_coherences.values()]
    
    # Calculate averages
    avg_coherence = {
        'mean_pairwise': np.mean(mean_pairwise_values),
        'min_pairwise': np.mean(min_pairwise_values),
        'centroid_tightness': np.mean(centroid_tightness_values),
        'loo_drift_deg': np.mean(loo_drift_values),
        'std_mean_pairwise': np.std(mean_pairwise_values),
        'std_min_pairwise': np.std(min_pairwise_values),
        'std_centroid_tightness': np.std(centroid_tightness_values),
        'std_loo_drift_deg': np.std(loo_drift_values)
    }
    
    return avg_coherence, author_coherences

def show_author_breakdown(author_coherences, top_n=10):
    """Show breakdown of individual authors"""
    print(f"\n📝 Top {top_n} authors by coherence (mean pairwise cosine):")
    print("-" * 80)
    
    # Sort by mean pairwise cosine
    sorted_authors = sorted(
        author_coherences.items(), 
        key=lambda x: x[1]['coherence']['mean_pairwise'], 
        reverse=True
    )
    
    for i, (author, data) in enumerate(sorted_authors[:top_n], 1):
        coherence = data['coherence']
        count = data['count']
        print(f"{i:2d}. {author:<20} ({count:2d} items) - "
              f"Mean: {coherence['mean_pairwise']:.3f}, "
              f"Min: {coherence['min_pairwise']:.3f}, "
              f"Centroid: {coherence['centroid_tightness']:.3f}, "
              f"LOO: {coherence['loo_drift_deg']:.1f}°")
    
    if len(sorted_authors) > top_n:
        print(f"    ... and {len(sorted_authors) - top_n} more authors")

def main():
    """Main function to test author coherence"""
    print("🧪 Testing Average Author Coherence")
    print("=" * 40)
    
    try:
        # Get all embeddings
        embeddings, poems = get_all_embeddings()
        
        if len(embeddings) == 0:
            print("❌ No embeddings found!")
            return
        
        # Analyze author coherence
        author_coherences = analyze_author_coherence(embeddings, poems, min_items=2)
        
        if not author_coherences:
            print("❌ No authors with sufficient items found!")
            return
        
        # Calculate average coherence
        avg_coherence, author_coherences = calculate_average_coherence(author_coherences)
        
        if avg_coherence is None:
            return
        
        # Display results
        print(f"\n📊 Average Coherence Across All Authors:")
        print(f"   - Mean pairwise cosine: {avg_coherence['mean_pairwise']:.4f} ± {avg_coherence['std_mean_pairwise']:.4f}")
        print(f"   - Min pairwise cosine: {avg_coherence['min_pairwise']:.4f} ± {avg_coherence['std_min_pairwise']:.4f}")
        print(f"   - Centroid tightness: {avg_coherence['centroid_tightness']:.4f} ± {avg_coherence['std_centroid_tightness']:.4f}")
        print(f"   - LOO drift (degrees): {avg_coherence['loo_drift_deg']:.2f} ± {avg_coherence['std_loo_drift_deg']:.2f}")
        
        # Show individual author breakdown
        show_author_breakdown(author_coherences, top_n=15)
        
        # Interpretation
        print(f"\n📈 Interpretation:")
        print(f"   - Average author coherence: {avg_coherence['mean_pairwise']:.3f}")
        if avg_coherence['mean_pairwise'] > 0.4:
            print(f"   ✅ High author coherence - authors have distinct, consistent styles")
        elif avg_coherence['mean_pairwise'] > 0.3:
            print(f"   ⚠️  Moderate author coherence - some author consistency")
        else:
            print(f"   ❌ Low author coherence - limited author-specific clustering")
        
        print(f"\n🎉 Author coherence analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during author coherence analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
