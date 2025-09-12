#!/usr/bin/env python3
"""
Test embedding coherence to analyze the quality and clustering of embeddings
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

def analyze_coherence_by_type(embeddings, poems):
    """Analyze coherence separately for poems vs quotes"""
    print("\n📊 Analyzing coherence by type...")
    
    # Separate by type
    poem_indices = [i for i, p in enumerate(poems) if p.get('type') == 'poem']
    quote_indices = [i for i, p in enumerate(poems) if p.get('type') == 'quote']
    other_indices = [i for i, p in enumerate(poems) if p.get('type') not in ['poem', 'quote']]
    
    print(f"   - Poems: {len(poem_indices)}")
    print(f"   - Quotes: {len(quote_indices)}")
    print(f"   - Other: {len(other_indices)}")
    
    results = {}
    
    # Overall coherence
    if len(embeddings) > 0:
        print("\n🔍 Overall coherence...")
        overall_coherence = embedding_coherence(embeddings)
        results['overall'] = overall_coherence
        print(f"   - Mean pairwise cosine: {overall_coherence['mean_pairwise']:.4f}")
        print(f"   - Min pairwise cosine: {overall_coherence['min_pairwise']:.4f}")
        print(f"   - Centroid tightness: {overall_coherence['centroid_tightness']:.4f}")
        print(f"   - LOO drift (degrees): {overall_coherence['loo_drift_deg']:.2f}")
    
    # Poems only
    if len(poem_indices) > 1:
        print("\n🔍 Poems coherence...")
        poem_embeddings = embeddings[poem_indices]
        poem_coherence = embedding_coherence(poem_embeddings)
        results['poems'] = poem_coherence
        print(f"   - Mean pairwise cosine: {poem_coherence['mean_pairwise']:.4f}")
        print(f"   - Min pairwise cosine: {poem_coherence['min_pairwise']:.4f}")
        print(f"   - Centroid tightness: {poem_coherence['centroid_tightness']:.4f}")
        print(f"   - LOO drift (degrees): {poem_coherence['loo_drift_deg']:.2f}")
    
    # Quotes only
    if len(quote_indices) > 1:
        print("\n🔍 Quotes coherence...")
        quote_embeddings = embeddings[quote_indices]
        quote_coherence = embedding_coherence(quote_embeddings)
        results['quotes'] = quote_coherence
        print(f"   - Mean pairwise cosine: {quote_coherence['mean_pairwise']:.4f}")
        print(f"   - Min pairwise cosine: {quote_coherence['min_pairwise']:.4f}")
        print(f"   - Centroid tightness: {quote_coherence['centroid_tightness']:.4f}")
        print(f"   - LOO drift (degrees): {quote_coherence['loo_drift_deg']:.2f}")
    
    return results

def analyze_coherence_by_author(embeddings, poems, top_authors=5):
    """Analyze coherence for top authors"""
    print(f"\n📊 Analyzing coherence by top {top_authors} authors...")
    
    # Count poems by author
    author_counts = {}
    for poem in poems:
        author = poem.get('author', 'Unknown')
        author_counts[author] = author_counts.get(author, 0) + 1
    
    # Get top authors
    top_authors_list = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:top_authors]
    
    results = {}
    
    for author, count in top_authors_list:
        if count < 2:  # Need at least 2 items for coherence
            continue
            
        print(f"\n🔍 {author} ({count} items)...")
        
        # Get indices for this author
        author_indices = [i for i, p in enumerate(poems) if p.get('author') == author]
        author_embeddings = embeddings[author_indices]
        
        if len(author_embeddings) > 1:
            author_coherence = embedding_coherence(author_embeddings)
            results[author] = author_coherence
            print(f"   - Mean pairwise cosine: {author_coherence['mean_pairwise']:.4f}")
            print(f"   - Min pairwise cosine: {author_coherence['min_pairwise']:.4f}")
            print(f"   - Centroid tightness: {author_coherence['centroid_tightness']:.4f}")
            print(f"   - LOO drift (degrees): {author_coherence['loo_drift_deg']:.2f}")
    
    return results

def interpret_coherence_results(results):
    """Interpret the coherence results"""
    print("\n📈 Coherence Interpretation:")
    print("=" * 50)
    
    print("\n🔍 What these metrics mean:")
    print("   - Mean pairwise cosine: Average similarity between all pairs")
    print("     • Higher = more similar overall (0.0-1.0)")
    print("     • 0.0 = orthogonal, 1.0 = identical")
    print("   - Min pairwise cosine: Lowest similarity between any pair")
    print("     • Higher = more consistent (no very different items)")
    print("   - Centroid tightness: How close items are to the center")
    print("     • Higher = more clustered around center")
    print("   - LOO drift: How much the centroid changes when removing one item")
    print("     • Lower = more stable, less sensitive to outliers")
    
    print("\n📊 Quality Assessment:")
    
    for category, metrics in results.items():
        print(f"\n{category.upper()}:")
        
        # Mean pairwise cosine interpretation
        mpc = metrics['mean_pairwise']
        if mpc > 0.7:
            print(f"   ✅ High similarity ({mpc:.3f}) - very coherent")
        elif mpc > 0.5:
            print(f"   ⚠️  Medium similarity ({mpc:.3f}) - moderately coherent")
        else:
            print(f"   ❌ Low similarity ({mpc:.3f}) - not very coherent")
        
        # Min pairwise cosine interpretation
        min_cos = metrics['min_pairwise']
        if min_cos > 0.3:
            print(f"   ✅ Consistent ({min_cos:.3f}) - no very different items")
        elif min_cos > 0.1:
            print(f"   ⚠️  Some outliers ({min_cos:.3f}) - a few different items")
        else:
            print(f"   ❌ Many outliers ({min_cos:.3f}) - very diverse items")
        
        # Centroid tightness interpretation
        ct = metrics['centroid_tightness']
        if ct > 0.7:
            print(f"   ✅ Tight clustering ({ct:.3f}) - well-centered")
        elif ct > 0.5:
            print(f"   ⚠️  Moderate clustering ({ct:.3f}) - somewhat centered")
        else:
            print(f"   ❌ Loose clustering ({ct:.3f}) - not well-centered")
        
        # LOO drift interpretation
        loo = metrics['loo_drift_deg']
        if loo < 10:
            print(f"   ✅ Stable ({loo:.1f}°) - robust to outliers")
        elif loo < 30:
            print(f"   ⚠️  Some sensitivity ({loo:.1f}°) - moderate robustness")
        else:
            print(f"   ❌ Sensitive ({loo:.1f}°) - sensitive to outliers")

def main():
    """Main function to test embedding coherence"""
    print("🧪 Testing Embedding Coherence")
    print("=" * 40)
    
    try:
        # Get all embeddings
        embeddings, poems = get_all_embeddings()
        
        if len(embeddings) == 0:
            print("❌ No embeddings found!")
            return
        
        print(f"\n📊 Dataset Info:")
        print(f"   - Total items: {len(embeddings)}")
        print(f"   - Embedding dimension: {embeddings.shape[1]}")
        
        # Analyze overall coherence
        print(f"\n🔍 Overall Coherence Analysis...")
        overall_coherence = embedding_coherence(embeddings)
        print(f"   - Mean pairwise cosine: {overall_coherence['mean_pairwise']:.4f}")
        print(f"   - Min pairwise cosine: {overall_coherence['min_pairwise']:.4f}")
        print(f"   - Centroid tightness: {overall_coherence['centroid_tightness']:.4f}")
        print(f"   - LOO drift (degrees): {overall_coherence['loo_drift_deg']:.2f}")
        
        # Analyze by type
        type_results = analyze_coherence_by_type(embeddings, poems)
        
        # Analyze by author
        author_results = analyze_coherence_by_author(embeddings, poems)
        
        # Combine results
        all_results = {
            'overall': overall_coherence,
            **type_results,
            **author_results
        }
        
        # Interpret results
        interpret_coherence_results(all_results)
        
        print(f"\n🎉 Coherence analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during coherence analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
