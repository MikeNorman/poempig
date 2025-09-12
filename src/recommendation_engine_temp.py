"""
Recommendation Engine Module

This module provides functionality to recommend poems based on similarity
using OpenAI embeddings and Supabase for storage.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv
import backoff
from tqdm import tqdm

# Load environment variables
load_dotenv()

class PoemRecommendationEngine:
    """Engine for recommending poems based on similarity."""
    
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Cache for embeddings
        self.embeddings_cache = {}
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using OpenAI API.
        
        Args:
            text (str): Text to embed
            
        Returns:
            List[float]: Embedding vector
        """
        # Check cache first
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            self.embeddings_cache[text] = embedding
            return embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise
    
    def add_poem_to_database(self, poem_data: Dict[str, Any]) -> str:
        """
        Add a poem to the Supabase database.
        
        Args:
            poem_data (dict): Poem data including text, title, author, etc.
            
        Returns:
            str: ID of the inserted poem
        """
        # Get embedding for the poem text
        poem_text = poem_data.get('text', '')
        embedding = self.get_embedding(poem_text)
        
        # Prepare data for database
        db_data = {
            'title': poem_data.get('title', ''),
            'author': poem_data.get('author', ''),
            'text': poem_text,
            'embedding': embedding,
            'metadata': json.dumps(poem_data.get('metadata', {}))
        }
        
        try:
            result = self.supabase.table('poems').insert(db_data).execute()
            if result.data:
                return result.data[0]['id']
            else:
                raise Exception("Failed to insert poem")
        except Exception as e:
            print(f"Error adding poem to database: {e}")
            raise
    
    def get_poem_embeddings(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all poems with their embeddings from the database using pagination.
        
        Args:
            limit (int): Maximum number of poems to retrieve (None for all)
            
        Returns:
            List[Dict]: List of poems with embeddings
        """
        try:
            all_poems = []
            page_size = 1000
            offset = 0
            
            while True:
                # Get page of poems
                result = self.supabase.table('poems').select('*').range(offset, offset + page_size - 1).execute()
                
                if not result.data or len(result.data) == 0:
                    break
                
                all_poems.extend(result.data)
                
                # Check if we got fewer than requested (last page)
                if len(result.data) < page_size:
                    break
                
                # Apply limit if specified
                if limit and len(all_poems) >= limit:
                    all_poems = all_poems[:limit]
                    break
                
                offset += page_size
            
            return all_poems
            
        except Exception as e:
            print(f"Error getting poems from database: {e}")
            return []
    
    def find_similar_poems(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar poems based on text similarity.
        
        Args:
            query_text (str): Text to find similar poems for
            top_k (int): Number of similar poems to return
            
        Returns:
            List[Dict]: List of similar poems with similarity scores
        """
        # Get embedding for query text
        query_embedding = self.get_embedding(query_text)
        
        # Get all poems from database
        poems = self.get_poem_embeddings()
        
        if not poems:
            return []
        
        # Calculate similarities
        similarities = []
        for poem in poems:
            if poem.get('embedding'):
                # Convert embedding to numpy array if it's a string
                if isinstance(poem['embedding'], str):
                    poem_embedding = json.loads(poem['embedding'])
                else:
                    poem_embedding = poem['embedding']
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, poem_embedding)
                similarities.append({
                    'poem': poem,
                    'similarity': similarity
                })
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    def recommend_by_theme(self, theme: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend poems by theme.
        
        Args:
            theme (str): Theme to search for
            top_k (int): Number of recommendations
            
        Returns:
            List[Dict]: List of recommended poems
        """
        # Create a query that includes the theme
        query = f"poems about {theme} poetry {theme} theme"
        return self.find_similar_poems(query, top_k)
    
    def recommend_by_author(self, author: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend poems by the same author.
        
        Args:
            author (str): Author name
            top_k (int): Number of recommendations
            
        Returns:
            List[Dict]: List of poems by the author
        """
        try:
            result = self.supabase.table('poems').select('*').eq('author', author).limit(top_k).execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting poems by author: {e}")
            return []
    
    def recommend_by_mood(self, mood: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend poems by mood/emotion.
        
        Args:
            mood (str): Mood/emotion to search for
            top_k (int): Number of recommendations
            
        Returns:
            List[Dict]: List of recommended poems
        """
        # Create a query that includes mood-related terms
        mood_queries = {
            'happy': 'joyful cheerful happy uplifting bright',
            'sad': 'melancholy sad sorrowful mournful dark',
            'romantic': 'love romantic passion heart beloved',
            'mysterious': 'mystery mysterious enigmatic secret hidden',
            'peaceful': 'calm peaceful serene tranquil quiet',
            'energetic': 'energetic dynamic vibrant lively spirited'
        }
        
        query = mood_queries.get(mood.lower(), mood)
        return self.find_similar_poems(query, top_k)
    
    def batch_process_poems(self, poems_data: List[Dict[str, Any]]) -> List[str]:
        """
        Process multiple poems in batch.
        
        Args:
            poems_data (List[Dict]): List of poem data dictionaries
            
        Returns:
            List[str]: List of inserted poem IDs
        """
        inserted_ids = []
        
        for poem_data in tqdm(poems_data, desc="Processing poems"):
            try:
                poem_id = self.add_poem_to_database(poem_data)
                inserted_ids.append(poem_id)
            except Exception as e:
                print(f"Error processing poem '{poem_data.get('title', 'Unknown')}': {e}")
                continue
        
        return inserted_ids
    
    def search_poems(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search poems using text similarity.
        
        Args:
            query (str): Search query
            top_k (int): Number of results to return
            
        Returns:
            List[Dict]: List of matching poems
        """
        return self.find_similar_poems(query, top_k)
    
    def get_poem_by_id(self, poem_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific poem by ID.
        
        Args:
            poem_id (str): ID of the poem
            
        Returns:
            Optional[Dict]: Poem data or None if not found
        """
        try:
            result = self.supabase.table('poems').select('*').eq('id', poem_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error getting poem by ID: {e}")
            return None
