#!/usr/bin/env python3
"""
Test specific authors: Hafez, Rumi, Mary Oliver, Nizar Qabbani, Rilke, Neruda
Calculate mean centroid tightness and MPCS for each
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
    # L2 normalize each row
    X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
    
    # pairwise cosines
    sims = X_norm @ X_norm.T
    iu = np.triu_indices(len(X_norm), 1)
    mpc = float(sims[iu].mean()) if len(iu[0]) else 1.0
    min_cos = float(sims[iu].min()) if len(iu[0]) else 1.0
    
    # centroid tightness
    c = X_norm.mean(0)
    c /= (np.linalg.norm(c) + 1e-12)
    ct = float((X_norm @ c).mean())
    
    # leave-one-out centroid drift (in degrees)
    if len(X_norm) > 2:
        drifts = []
        sumX = X_norm.sum(0)
        for i in range(len(X_norm)):
            ci = (sumX - X_norm[i]) / (len(X_norm)-1)
            ci /= (np.linalg.norm(ci) + 1e-12)
            drifts.append(np.degrees(np.arccos(np.clip(c @ ci, -1, 1))))
        loo_deg = float(max(drifts))
    else:
        loo_deg = 0.0
    
    return {"mean_pairwise": mpc, "min_pairwise": min_cos, "centroid_tightness": ct, "loo_drift_deg": loo_deg}

def get_author_embeddings(embeddings, poems, target_authors):
    """Get embeddings for specific authors"""
    print(f"🔍 Getting embeddings for specific authors...")
    
    author_embeddings = {}
    
    for i, poem in enumerate(poems):
        author = poem.get('author', '').strip()
        if author in target_authors:
            if author not in author_embeddings:
                author_embeddings[author] = []
            author_embeddings[author].append(embeddings[i])
    
    # Convert to numpy arrays
    for author in author_embeddings:
        author_embeddings[author] = np.array(author_embeddings[author])
    
    return author_embeddings

def analyze_specific_authors(author_embeddings, target_authors):
    """Analyze coherence for specific authors"""
    print(f"\n📊 Specific Author Analysis:")
    print(f"   - Target authors: {', '.join(target_authors)}")
    
    results = {}
    
    for author in target_authors:
        if author in author_embeddings:
            embeddings = author_embeddings[author]
            count = len(embeddings)
            
            print(f"\n📝 {author} ({count} items):")
            
            if count >= 2:
                coherence = embedding_coherence(embeddings)
                
                print(f"   - Mean Pairwise Cosine Similarity (MPCS): {coherence['mean_pairwise']:.4f}")
                print(f"   - Centroid Tightness: {coherence['centroid_tightness']:.4f}")
                print(f"   - Min Pairwise Cosine: {coherence['min_pairwise']:.4f}")
                print(f"   - LOO Drift (degrees): {coherence['loo_drift_deg']:.2f}")
                
                results[author] = {
                    'count': count,
                    'mpcs': coherence['mean_pairwise'],
                    'centroid_tightness': coherence['centroid_tightness'],
                    'min_pairwise': coherence['min_pairwise'],
                    'loo_drift_deg': coherence['loo_drift_deg']
                }
            else:
                print(f"   - Not enough items for analysis (need at least 2)")
                results[author] = {
                    'count': count,
                    'mpcs': None,
                    'centroid_tightness': None,
                    'min_pairwise': None,
                    'loo_drift_deg': None
                }
        else:
            print(f"\n📝 {author}: Not found in database")
            results[author] = {
                'count': 0,
                'mpcs': None,
                'centroid_tightness': None,
                'min_pairwise': None,
                'loo_drift_deg': None
            }
    
    return results

def show_summary_table(results, target_authors):
    """Show summary table of results"""
    print(f"\n📊 Summary Table:")
    print("=" * 80)
    print(f"{'Author':<20} {'Count':<8} {'MPCS':<8} {'Centroid':<8} {'Min Cos':<8} {'LOO Drift':<10}")
    print("-" * 80)
    
    for author in target_authors:
        if author in results:
            r = results[author]
            count = r['count']
            mpcs = f"{r['mpcs']:.4f}" if r['mpcs'] is not None else "N/A"
            centroid = f"{r['centroid_tightness']:.4f}" if r['centroid_tightness'] is not None else "N/A"
            min_cos = f"{r['min_pairwise']:.4f}" if r['min_pairwise'] is not None else "N/A"
            loo_drift = f"{r['loo_drift_deg']:.2f}°" if r['loo_drift_deg'] is not None else "N/A"
            
            print(f"{author:<20} {count:<8} {mpcs:<8} {centroid:<8} {min_cos:<8} {loo_drift:<10}")

def main():
    """Main function to analyze specific authors"""
    print("🧪 Analyzing Specific Authors")
    print("=" * 50)
    
    # Target authors
    target_authors = ['Hafiz', 'Rumi', 'Mary Oliver', 'Nizar Qabbani', 'Rilke', 'Neruda']
    
    try:
        # Get all embeddings
        engine = PoemRecommendationEngine()
        all_poems = engine.get_poem_embeddings()
        
        print(f"📊 Retrieved {len(all_poems)} poems")
        
        # Extract embeddings
        embeddings = []
        valid_poems = []
        
        for poem in all_poems:
            embedding = poem.get('embedding')
            if embedding is not None:
                if isinstance(embedding, str):
                    try:
                        embedding = json.loads(embedding)
                    except:
                        continue
                elif isinstance(embedding, list):
                    pass
                else:
                    continue
                    
                embeddings.append(embedding)
                valid_poems.append(poem)
        
        embeddings = np.array(embeddings)
        print(f"✅ Found {len(embeddings)} valid embeddings")
        
        # Get embeddings for target authors
        author_embeddings = get_author_embeddings(embeddings, valid_poems, target_authors)
        
        # Analyze each author
        results = analyze_specific_authors(author_embeddings, target_authors)
        
        # Show summary table
        show_summary_table(results, target_authors)
        
        print(f"\n🎉 Specific author analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
