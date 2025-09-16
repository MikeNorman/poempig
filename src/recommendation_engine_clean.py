"""
Clean Recommendation Engine Module

This module provides simple keyword and semantic search functionality.
No vectors, no top_k, no complexity.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PoemRecommendationEngine:
    """Simple engine for searching poems using keyword and semantic search."""
    
    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def search_poems(self, query: str) -> List[Dict[str, Any]]:
        """
        Search poems using keyword search for quoted phrases and semantic search for natural language.
        
        Args:
            query (str): Search query
            
        Returns:
            List[Dict]: List of matching poems
        """
        # Extract quoted phrases and natural language parts
        quoted_phrases = re.findall(r'"([^"]*)"', query)
        natural_language = re.sub(r'"[^"]*"', '', query).strip()
        
        all_results = []
        
        # 1. Keyword search for quoted phrases (exact matches)
        if quoted_phrases:
            for phrase in quoted_phrases:
                keyword_results = self._search_by_keywords(phrase)
                all_results.extend(keyword_results)
        
        # 2. Semantic search for natural language (text-based matching)
        if natural_language:
            semantic_results = self._search_by_semantic_similarity(natural_language)
            all_results.extend(semantic_results)
        
        # 3. Fallback: if no natural language, do keyword search on the whole query
        if not natural_language and not quoted_phrases:
            keyword_results = self._search_by_keywords(query)
            all_results.extend(keyword_results)
        
        # Remove duplicates and sort by relevance
        unique_results = {}
        for result in all_results:
            poem_id = result['poem']['id']
            if poem_id not in unique_results or unique_results[poem_id]['similarity'] < result['similarity']:
                unique_results[poem_id] = result
        
        # Return all results sorted by similarity
        final_results = list(unique_results.values())
        final_results.sort(key=lambda x: x['similarity'], reverse=True)
        return final_results
    
    def _search_by_keywords(self, keywords: str) -> List[Dict[str, Any]]:
        """
        Search poems by exact keyword matching in title, author, and text.
        
        Args:
            keywords (str): Keywords to search for
            
        Returns:
            List[Dict]: List of matching poems with relevance scores
        """
        try:
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
            
            # Return all results sorted by similarity
            final_results = list(poem_scores.values())
            final_results.sort(key=lambda x: x['similarity'], reverse=True)
            return final_results
            
        except Exception as e:
            print(f"Error in keyword search: {e}")
            return []
    
    def _search_by_semantic_similarity(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Search poems using semantic similarity (text-based matching).
        
        Args:
            query_text (str): Text to find similar poems for
            
        Returns:
            List[Dict]: List of similar poems with similarity scores
        """
        try:
            # Get all poems from database
            poems = self.supabase.table('poems').select('*').execute()
            
            if not poems.data:
                return []
            
            # Split query into words for semantic matching
            query_words = set(query_text.lower().split())
            
            results = []
            for poem in poems.data:
                # Combine title, author, and text for semantic matching
                searchable_text = f"{poem.get('title', '')} {poem.get('author', '')} {poem.get('text', '')}".lower()
                
                # Calculate word overlap similarity
                poem_words = set(searchable_text.split())
                common_words = query_words.intersection(poem_words)
                
                if common_words:  # Only include poems with some word overlap
                    # Calculate similarity score based on word overlap
                    similarity = len(common_words) / len(query_words.union(poem_words))
                    
                    results.append({
                        'poem': poem,
                        'similarity': similarity,
                        'match_type': 'semantic'
                    })
            
            # Sort by similarity and return all results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
    
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
