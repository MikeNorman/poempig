"""
Recommendation Engine Module

This module provides functionality to recommend poems based on similarity                                           
using OpenAI embeddings and Supabase for storage.
"""

import os
import json
import numpy as np
import re
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
            limit (int): Maximum number of poems to retrieve
            
        Returns:
            List[Dict]: List of poems with embeddings
        """
        poems = []
        page_size = 1000
        offset = 0
        
        while True:
            try:
                query = self.supabase.table('poems').select('*').range(offset, offset + page_size - 1)
                result = query.execute()
                
                if not result.data:
                    break
                    
                poems.extend(result.data)
                offset += page_size
                
                if limit and len(poems) >= limit:
                    poems = poems[:limit]
                    break
                    
            except Exception as e:
                print(f"Error fetching poems: {e}")
                break
        
        return poems
    
    def find_similar_poems(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:                          
        """
        Find similar poems based on text similarity using Supabase vector search.
        
        Args:
            query_text (str): Text to find similar poems for                                                        
            top_k (int): Number of similar poems to return
            
        Returns:
            List[Dict]: List of similar poems with similarity scores                                                
        """
        try:
            # Get embedding for query text
            query_embedding = self.get_embedding(query_text)
            
            # Convert to string for Supabase RPC call
            vector_str = json.dumps(query_embedding)
            
            # Use Supabase vector search for fast results (same as vibe profile search)
            result = self.supabase.rpc('match_poems', {
                'q': vector_str,
                'match_count': 50  # Get more results to ensure we have enough
            }).execute()
            
            if result.data:
                # Convert results to our expected format (same as vibe profile search)
                similarities = []
                for item in result.data[:top_k]:
                    similarities.append({
                        'poem': item,  # Use the entire poem object from Supabase
                        'similarity': float(item.get('similarity', 0.0))
                    })
                return similarities
            else:
                return []
                
        except Exception as e:
            print(f"Vector search failed, falling back to manual search: {e}")
            # Fallback to manual search if vector search fails
            return self._manual_similarity_search(query_text, top_k)
    
    def _manual_similarity_search(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Fallback manual similarity search with optimization."""
        # Get embedding for query text
        query_embedding = self.get_embedding(query_text)
        
        # Get a sample of poems from database (limit to 200 for speed)
        poems = self.get_poem_embeddings(limit=200)
        
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
                similarity = np.dot(query_embedding, poem_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(poem_embedding)
                )
                
                similarities.append({
                    'poem': poem,
                    'similarity': similarity
                })
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def find_similar_by_poem_id(self, poem_id: str, top_k: int = 5, exclude_poem_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        Find similar poems based on an existing poem's embedding.
        This method uses the existing embedding from the database instead of re-embedding.
        
        Args:
            poem_id (str): ID of the poem to find similar poems for
            top_k (int): Number of similar poems to return
            exclude_poem_ids (List[str]): List of poem IDs to exclude from results
            
        Returns:
            List[Dict]: List of similar poems with similarity scores
        """
        # Get the source poem by ID
        source_poem = self.get_poem_by_id(poem_id)
        if not source_poem or not source_poem.get('embedding'):
            return []
        
        # Get the source poem's embedding
        if isinstance(source_poem['embedding'], str):
            source_embedding = json.loads(source_poem['embedding'])
        else:
            source_embedding = source_poem['embedding']
        
        # Get all poems from database
        poems = self.get_poem_embeddings()
        
        if not poems:
            return []
        
        # Create set of excluded poem IDs for faster lookup
        excluded_ids = set(exclude_poem_ids or [])
        excluded_ids.add(poem_id)  # Always exclude the source poem itself
        
        # Calculate similarities
        similarities = []
        for poem in poems:
            # Skip excluded poems (including the source poem itself)
            if poem['id'] in excluded_ids:
                continue
                
            if poem.get('embedding'):
                # Convert embedding to numpy array if it's a string
                if isinstance(poem['embedding'], str):
                    poem_embedding = json.loads(poem['embedding'])
                else:
                    poem_embedding = poem['embedding']
                
                # Calculate cosine similarity
                similarity = np.dot(source_embedding, poem_embedding) / (
                    np.linalg.norm(source_embedding) * np.linalg.norm(poem_embedding)
                )
                
                similarities.append({
                    'poem': poem,
                    'similarity': similarity
                })
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def search_poems_by_exact_keywords(self, keywords: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search poems using exact keyword matching in title, author, and text.
        
        Args:
            keywords (str): Keywords to search for
            top_k (int): Number of results to return
            
        Returns:
            List[Dict]: List of matching poems with relevance scores
        """
        try:
            # Search in title, author, and text using Supabase ilike for case-insensitive matching
            results = []
            
            # Search in title
            title_matches = self.supabase.table('poems').select('*').ilike('title', f'%{keywords}%').execute()
            if title_matches.data:
                for poem in title_matches.data:
                    results.append({
                        'poem': poem,
                        'similarity': 1.0,  # High relevance for title matches
                        'match_type': 'title'
                    })
            
            # Search in author
            author_matches = self.supabase.table('poems').select('*').ilike('author', f'%{keywords}%').execute()
            if author_matches.data:
                for poem in author_matches.data:
                    results.append({
                        'poem': poem,
                        'similarity': 0.9,  # High relevance for author matches
                        'match_type': 'author'
                    })
            
            # Search in text
            text_matches = self.supabase.table('poems').select('*').ilike('text', f'%{keywords}%').execute()
            if text_matches.data:
                for poem in text_matches.data:
                    results.append({
                        'poem': poem,
                        'similarity': 0.8,  # Lower relevance for text matches
                        'match_type': 'text'
                    })
            
            # Remove duplicates and sort by relevance
            poem_scores = {}
            for result in results:
                poem_id = result['poem']['id']
                if poem_id not in poem_scores or poem_scores[poem_id]['similarity'] < result['similarity']:
                    poem_scores[poem_id] = result
            
            # Convert to list and sort by similarity
            final_results = list(poem_scores.values())
            final_results.sort(key=lambda x: x['similarity'], reverse=True)
            return final_results[:top_k]
            
        except Exception as e:
            print(f"Error in exact keyword search: {e}")
            return []
    
    def search_poems(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:                                    
        """
        Search poems using both exact keyword matching and semantic similarity.
        
        Args:
            query (str): Search query
            top_k (int): Number of results to return
            
        Returns:
            List[Dict]: List of matching poems
        """
        # Extract quoted phrases and natural language parts
        quoted_phrases = re.findall(r'"([^"]*)"', query)
        natural_language = re.sub(r'"[^"]*"', '', query).strip()
        
        results = []
        
        # 1. Exact keyword search for quoted phrases
        if quoted_phrases:
            for phrase in quoted_phrases:
                exact_results = self.search_poems_by_exact_keywords(phrase, top_k)
                results.extend(exact_results)
        
        # 2. Semantic search for natural language (prioritize this for speed)
        if natural_language:
            semantic_results = self.find_similar_poems(natural_language, top_k)
            results.extend(semantic_results)
        
        # 3. Only do exact search if we have quoted phrases or very short queries
        if quoted_phrases or (not natural_language and len(query.strip()) <= 3):
            exact_results = self.search_poems_by_exact_keywords(query, top_k)
            results.extend(exact_results)
        
        # Remove duplicates and combine scores
        poem_scores = {}
        for result in results:
            poem_id = result['poem']['id']
            if poem_id not in poem_scores or poem_scores[poem_id]['similarity'] < result['similarity']:
                poem_scores[poem_id] = result
        
        # Convert to final results and sort
        final_results = list(poem_scores.values())
        final_results.sort(key=lambda x: x['similarity'], reverse=True)
        return final_results[:top_k]
    
    def get_poem_by_id(self, poem_id: str) -> Optional[Dict[str, Any]]:                                             
        """
        Get a specific poem by ID.
        
        Args:
            poem_id (str): ID of the poem
            
        Returns:
            Dict: Poem data or None if not found
        """
        try:
            result = self.supabase.table('poems').select('*').eq('id', poem_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error getting poem by ID: {e}")
            return None
    
    def recommend_by_theme(self, theme: str, top_k: int = 5) -> List[Dict[str, Any]]:                               
        """
        Recommend poems by theme.
        
        Args:
            theme (str): Theme to search for
            top_k (int): Number of recommendations
            
        Returns:
            List[Dict]: List of recommended poems
        """
        return self.find_similar_poems(f"poems about {theme}", top_k)
    
    def recommend_by_mood(self, mood: str, top_k: int = 5) -> List[Dict[str, Any]]:                                 
        """
        Recommend poems by mood.
        
        Args:
            mood (str): Mood to search for
            top_k (int): Number of recommendations
            
        Returns:
            List[Dict]: List of recommended poems
        """
        return self.find_similar_poems(f"{mood} poems", top_k)
    
    def recommend_by_author(self, author: str, top_k: int = 5) -> List[Dict[str, Any]]:                             
        """
        Recommend poems by author.
        
        Args:
            author (str): Author name
            top_k (int): Number of recommendations
            
        Returns:
            List[Dict]: List of recommended poems
        """
        return self.find_similar_poems(f"poems by {author}", top_k)
    
    def add_poems_batch(self, poems_data: List[Dict[str, Any]]) -> List[str]:                                       
        """
        Add multiple poems to the database in batch.
        
        Args:
            poems_data (List[Dict]): List of poem data
            
        Returns:
            List[str]: List of inserted poem IDs
        """
        inserted_ids = []
        
        for poem_data in tqdm(poems_data, desc="Adding poems"):
            try:
                poem_id = self.add_poem_to_database(poem_data)
                inserted_ids.append(poem_id)
            except Exception as e:
                print(f"Error adding poem: {e}")
                continue
        
        return inserted_ids
