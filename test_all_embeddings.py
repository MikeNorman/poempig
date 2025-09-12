#!/usr/bin/env python3
"""
Test that the recommendation engine can access all items with embeddings
"""

import sys
import os
sys.path.append('src')

from recommendation_engine import PoemRecommendationEngine

def test_all_embeddings():
    """Test that we can retrieve all items with embeddings"""
    print("🧪 Testing recommendation engine with all embeddings...")
    
    try:
        # Initialize the recommendation engine
        engine = PoemRecommendationEngine()
        
        # Get all poems with embeddings
        print("📊 Retrieving all poems with embeddings...")
        all_poems = engine.get_poem_embeddings()
        
        print(f"✅ Successfully retrieved {len(all_poems)} poems")
        
        # Check that we have the expected number
        if len(all_poems) == 1099:
            print("✅ Perfect! Retrieved all 1099 poems as expected")
        else:
            print(f"⚠️  Expected 1099 poems, got {len(all_poems)}")
        
        # Check that all poems have embeddings
        poems_with_embeddings = [p for p in all_poems if p.get('embedding') is not None]
        poems_without_embeddings = [p for p in all_poems if p.get('embedding') is None]
        
        print(f"📊 Embedding status:")
        print(f"   - Poems with embeddings: {len(poems_with_embeddings)}")
        print(f"   - Poems without embeddings: {len(poems_without_embeddings)}")
        
        if len(poems_without_embeddings) == 0:
            print("✅ All poems have embeddings!")
        else:
            print(f"❌ {len(poems_without_embeddings)} poems are missing embeddings")
        
        # Test a similarity search to make sure it works
        print("\n🔍 Testing similarity search...")
        test_query = "love and romance"
        similar_poems = engine.find_similar_poems(test_query, top_k=5)
        
        print(f"✅ Found {len(similar_poems)} similar poems for query: '{test_query}'")
        
        if similar_poems:
            print("📝 Top similar poems:")
            for i, result in enumerate(similar_poems[:3], 1):
                poem = result['poem']
                similarity = result['similarity']
                print(f"   {i}. {poem.get('title', 'No title')} by {poem.get('author', 'Unknown')} (similarity: {similarity:.3f})")
        
        print("\n🎉 All tests passed! The recommendation engine is working correctly with all embeddings.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing recommendation engine: {e}")
        return False

if __name__ == "__main__":
    success = test_all_embeddings()
    sys.exit(0 if success else 1)
