#!/usr/bin/env python3
"""
Test between-profile separation - how different are author profiles from one another
"""

import os
import sys
import numpy as np
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm
from itertools import combinations

# Add src to path
sys.path.append('src')
from recommendation_engine import PoemRecommendationEngine

load_dotenv()

def get_author_centroids(embeddings, poems, min_items=3):
    """Calculate centroid for each author with at least min_items"""
    print(f"🔍 Calculating author centroids (min {min_items} items)...")
    
    # Group by author (excluding null/empty authors)
    author_groups = {}
    for i, poem in enumerate(poems):
        author = poem.get('author', '').strip()
        if author and author.lower() not in ['unknown', 'null', 'none', '']:
            if author not in author_groups:
                author_groups[author] = []
            author_groups[author].append(i)
    
    # Filter authors with enough items
    valid_authors = {author: indices for author, indices in author_groups.items() if len(indices) >= min_items}
    print(f"📝 Found {len(valid_authors)} authors with at least {min_items} items")
    
    # Calculate centroids
    author_centroids = {}
    for author, indices in tqdm(valid_authors.items(), desc="Calculating centroids"):
        author_embeddings = embeddings[indices]
        
        # L2 normalize each embedding
        normalized_embeddings = author_embeddings / (np.linalg.norm(author_embeddings, axis=1, keepdims=True) + 1e-12)
        
        # Calculate centroid
        centroid = normalized_embeddings.mean(axis=0)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-12)  # L2 normalize centroid
        
        author_centroids[author] = {
            'centroid': centroid,
            'count': len(indices),
            'indices': indices
        }
    
    return author_centroids

def calculate_between_author_similarities(author_centroids):
    """Calculate pairwise similarities between author centroids"""
    print(f"🔍 Calculating between-author similarities...")
    
    authors = list(author_centroids.keys())
    centroids = np.array([author_centroids[author]['centroid'] for author in authors])
    
    # Calculate pairwise cosine similarities
    similarities = centroids @ centroids.T
    
    # Get upper triangle (excluding diagonal)
    n = len(authors)
    similarities_upper = []
    author_pairs = []
    
    for i in range(n):
        for j in range(i + 1, n):
            similarities_upper.append(similarities[i, j])
            author_pairs.append((authors[i], authors[j]))
    
    return similarities_upper, author_pairs, authors

def analyze_between_author_separation(similarities, author_pairs, authors):
    """Analyze the separation between author profiles"""
    print(f"\n📊 Between-Author Profile Separation Analysis:")
    print(f"   - Number of authors: {len(authors)}")
    print(f"   - Number of author pairs: {len(similarities)}")
    
    # Basic statistics
    mean_similarity = np.mean(similarities)
    std_similarity = np.std(similarities)
    min_similarity = np.min(similarities)
    max_similarity = np.max(similarities)
    median_similarity = np.median(similarities)
    
    print(f"\n📈 Similarity Statistics:")
    print(f"   - Mean similarity: {mean_similarity:.4f} ± {std_similarity:.4f}")
    print(f"   - Median similarity: {median_similarity:.4f}")
    print(f"   - Min similarity: {min_similarity:.4f}")
    print(f"   - Max similarity: {max_similarity:.4f}")
    print(f"   - Range: {max_similarity - min_similarity:.4f}")
    
    # Separation analysis
    separation = 1 - mean_similarity  # Higher separation = lower similarity
    print(f"\n🔍 Separation Analysis:")
    print(f"   - Average separation: {separation:.4f}")
    
    if separation > 0.7:
        print(f"   ✅ High separation - authors are very distinct")
    elif separation > 0.5:
        print(f"   ⚠️  Moderate separation - some author overlap")
    else:
        print(f"   ❌ Low separation - authors are quite similar")
    
    # Find most similar and most different pairs
    most_similar_idx = np.argmax(similarities)
    most_different_idx = np.argmin(similarities)
    
    print(f"\n📝 Most Similar Authors:")
    print(f"   - {author_pairs[most_similar_idx][0]} & {author_pairs[most_similar_idx][1]}: {similarities[most_similar_idx]:.4f}")
    
    print(f"\n📝 Most Different Authors:")
    print(f"   - {author_pairs[most_different_idx][0]} & {author_pairs[most_different_idx][1]}: {similarities[most_different_idx]:.4f}")
    
    return {
        'mean_similarity': mean_similarity,
        'std_similarity': std_similarity,
        'min_similarity': min_similarity,
        'max_similarity': max_similarity,
        'median_similarity': median_similarity,
        'separation': separation,
        'most_similar': (author_pairs[most_similar_idx], similarities[most_similar_idx]),
        'most_different': (author_pairs[most_different_idx], similarities[most_different_idx])
    }

def show_similarity_distribution(similarities, author_pairs, top_n=10):
    """Show distribution of similarities"""
    print(f"\n📊 Top {top_n} Most Similar Author Pairs:")
    print("-" * 60)
    
    # Get top similar pairs
    top_similar_indices = np.argsort(similarities)[-top_n:][::-1]
    
    for i, idx in enumerate(top_similar_indices, 1):
        author1, author2 = author_pairs[idx]
        similarity = similarities[idx]
        print(f"{i:2d}. {author1:<20} & {author2:<20}: {similarity:.4f}")
    
    print(f"\n📊 Top {top_n} Most Different Author Pairs:")
    print("-" * 60)
    
    # Get top different pairs
    top_different_indices = np.argsort(similarities)[:top_n]
    
    for i, idx in enumerate(top_different_indices, 1):
        author1, author2 = author_pairs[idx]
        similarity = similarities[idx]
        print(f"{i:2d}. {author1:<20} & {author2:<20}: {similarity:.4f}")

def analyze_author_clustering(author_centroids, similarities, authors, author_pairs):
    """Analyze how authors cluster together"""
    print(f"\n🔍 Author Clustering Analysis:")
    
    # Calculate pairwise distances (1 - similarity)
    distances = 1 - np.array(similarities)
    
    # Find authors that are very similar to each other (clusters)
    threshold = 0.8  # High similarity threshold
    similar_pairs = [(author_pairs[i], similarities[i]) for i, sim in enumerate(similarities) if sim > threshold]
    
    print(f"   - Pairs with similarity > {threshold}: {len(similar_pairs)}")
    
    if similar_pairs:
        print(f"   - High similarity pairs:")
        for (author1, author2), similarity in similar_pairs[:5]:  # Show top 5
            print(f"     • {author1} & {author2}: {similarity:.4f}")
    
    # Calculate average distance to nearest neighbor for each author
    centroids = np.array([author_centroids[author]['centroid'] for author in authors])
    centroid_similarities = centroids @ centroids.T
    
    nearest_neighbor_distances = []
    for i, author in enumerate(authors):
        # Get similarities to all other authors (exclude self)
        other_similarities = np.concatenate([centroid_similarities[i, :i], centroid_similarities[i, i+1:]])
        max_similarity = np.max(other_similarities)
        nearest_neighbor_distances.append(1 - max_similarity)
    
    avg_nearest_neighbor_distance = np.mean(nearest_neighbor_distances)
    print(f"   - Average distance to nearest neighbor: {avg_nearest_neighbor_distance:.4f}")
    
    return {
        'similar_pairs': similar_pairs,
        'avg_nearest_neighbor_distance': avg_nearest_neighbor_distance
    }

def main():
    """Main function to test between-author separation"""
    print("🧪 Testing Between-Author Profile Separation")
    print("=" * 50)
    
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
        
        # Calculate author centroids
        author_centroids = get_author_centroids(embeddings, valid_poems, min_items=3)
        
        if len(author_centroids) < 2:
            print("❌ Need at least 2 authors for separation analysis!")
            return
        
        # Calculate between-author similarities
        similarities, author_pairs, authors = calculate_between_author_similarities(author_centroids)
        
        # Analyze separation
        separation_stats = analyze_between_author_separation(similarities, author_pairs, authors)
        
        # Show similarity distribution
        show_similarity_distribution(similarities, author_pairs, top_n=10)
        
        # Analyze clustering
        clustering_stats = analyze_author_clustering(author_centroids, similarities, authors, author_pairs)
        
        # Final interpretation
        print(f"\n📈 Final Interpretation:")
        print(f"   - Author profiles are {separation_stats['separation']:.1%} separated on average")
        print(f"   - This means authors are {'very distinct' if separation_stats['separation'] > 0.7 else 'moderately distinct' if separation_stats['separation'] > 0.5 else 'somewhat similar'}")
        print(f"   - The embedding model {'successfully' if separation_stats['separation'] > 0.5 else 'partially'} captures author-specific styles")
        
        print(f"\n🎉 Between-author separation analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during separation analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
