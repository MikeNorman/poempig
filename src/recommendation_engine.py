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
from .semantic_tagger import SemanticTagger

# Load environment variables
load_dotenv()

class ItemRecommendationEngine:
    """Simple engine for searching items (poems and quotes) using keyword and semantic search."""
    
    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize semantic tagger
        self.tagger = SemanticTagger()
        
        # Initialize OpenAI client for embeddings
        from openai import OpenAI
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        
        # Cache for embeddings
        self.embeddings_cache = {}
    
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
            
            # Cache the embedding
            self.embeddings_cache[text] = embedding
            return embedding
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
        
    def search_items(self, query: str) -> List[Dict[str, Any]]:
        """
        Search items (poems and quotes) using keyword search for quoted phrases and semantic search for natural language.
        
        Args:
            query (str): Search query
            
        Returns:
            List[Dict]: List of matching items
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
        
        # 2. Keyword search for natural language (fallback to keyword search)
        if natural_language:
            keyword_results = self._search_by_keywords(natural_language)
            all_results.extend(keyword_results)
        
        # 3. Fallback: if no natural language, do keyword search on the whole query
        if not natural_language and not quoted_phrases:
            keyword_results = self._search_by_keywords(query)
            all_results.extend(keyword_results)
        
        # Remove duplicates and sort by relevance
        unique_results = {}
        for result in all_results:
            item_id = result['item']['id']
            if item_id not in unique_results or unique_results[item_id]['similarity'] < result['similarity']:
                unique_results[item_id] = result
        
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
            title_matches = self.supabase.table('items').select('*').ilike('title', f'%{keywords}%').execute()
            if title_matches.data:
                for item in title_matches.data:
                    results.append({
                        'item': item,
                        'similarity': 1.0,  # High relevance for title matches
                        'match_type': 'title'
                    })
            
            # Search in author
            author_matches = self.supabase.table('items').select('*').ilike('author', f'%{keywords}%').execute()
            if author_matches.data:
                for item in author_matches.data:
                    results.append({
                        'item': item,
                        'similarity': 0.9,  # High relevance for author matches
                        'match_type': 'author'
                    })
            
            # Search in text
            text_matches = self.supabase.table('items').select('*').ilike('text', f'%{keywords}%').execute()
            if text_matches.data:
                for item in text_matches.data:
                    results.append({
                        'item': item,
                        'similarity': 0.8,  # Lower relevance for text matches
                        'match_type': 'text'
                    })
            
            # Remove duplicates and sort by relevance
            unique_results = {}
            for result in results:
                item_id = result['item']['id']
                if item_id not in unique_results or unique_results[item_id]['similarity'] < result['similarity']:
                    unique_results[item_id] = result
            
            # Sort by similarity and return all results
            final_results = list(unique_results.values())
            final_results.sort(key=lambda x: x['similarity'], reverse=True)
            return final_results
            
        except Exception as e:
            print(f"Error in keyword search: {e}")
            return []
    
    def _search_by_semantic_similarity(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Search poems using semantic similarity based on tags.
        
        Args:
            query_text (str): Query text to search for
            
        Returns:
            List[Dict]: List of similar poems with similarity scores
        """
        try:
            # Convert query to semantic tags
            query_tags = self.tagger.get_search_tags(query_text)
            print(f"Search tags for '{query_text}': {query_tags}")
            
            # Search items that have any of the query tags
            results = []
            for tag in query_tags:
                # Use PostgreSQL array contains operator to find items with this tag
                items_result = self.supabase.table('items').select('*').contains('semantic_tags', [tag]).execute()
                
                if items_result.data:
                    for item in items_result.data:
                        item_tags = item.get('semantic_tags', [])
                        
                        # Parse structured tags if they exist
                        structured_tags = self._parse_structured_tags(item_tags)
                        
                        # Calculate similarity with relevance scoring
                        similarity, matched_tags = self._calculate_structured_similarity(query_tags, structured_tags)
                        
                        if similarity > 0:  # Only include items with some tag overlap
                            results.append({
                                'item': item,
                                'similarity': similarity,
                                'match_type': 'semantic',
                                'matched_tags': matched_tags
                            })
            
            # Remove duplicates and sort by similarity
            unique_results = {}
            for result in results:
                item_id = result['item']['id']
                if item_id not in unique_results or unique_results[item_id]['similarity'] < result['similarity']:
                    unique_results[item_id] = result
            
            # Sort by similarity and return all results
            final_results = list(unique_results.values())
            final_results.sort(key=lambda x: x['similarity'], reverse=True)
            return final_results
            
        except Exception as e:
            print(f"Error in keyword search: {e}")
            return []
    
    def _parse_structured_tags(self, tags_array: List[str]) -> Dict[str, List[Dict[str, float]]]:
        """Parse structured tags from the database array."""
        structured_tags = {
            "emotions": [],
            "themes": [],
            "imagery": [],
            "style": []
        }
        
        for tag_string in tags_array:
            try:
                import json
                if tag_string.startswith('{') and tag_string.endswith('}'):
                    # This is a structured tag
                    tag_data = json.loads(tag_string)
                    for category in structured_tags.keys():
                        if category in tag_data and isinstance(tag_data[category], list):
                            structured_tags[category].extend(tag_data[category])
                else:
                    # This is a simple string tag - convert to structured format
                    # Add to themes category with medium relevance
                    structured_tags["themes"].append({"tag": tag_string, "relevance": 0.5})
            except (json.JSONDecodeError, TypeError):
                # Invalid JSON or not a string - skip
                continue
        
        return structured_tags
    
    def _calculate_structured_similarity(self, query_tags: List[str], structured_tags: Dict[str, List[Dict[str, float]]]) -> tuple[float, List[str]]:
        """Calculate similarity between query tags and structured item tags."""
        query_tag_set = set(tag.lower() for tag in query_tags)
        matched_tags = []
        total_relevance = 0.0
        match_count = 0
        
        # Check all categories for matches
        for category, tag_list in structured_tags.items():
            for tag_info in tag_list:
                tag_name = tag_info.get('tag', '').lower()
                relevance = tag_info.get('relevance', 0.5)
                
                if tag_name in query_tag_set:
                    matched_tags.append(tag_name)
                    total_relevance += relevance
                    match_count += 1
        
        if match_count == 0:
            return 0.0, []
        
        # Calculate weighted similarity score
        # Higher relevance matches get more weight
        similarity = total_relevance / len(query_tag_set) if query_tag_set else 0.0
        
        return similarity, matched_tags
    
    def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific item by ID.
        
        Args:
            item_id (str): ID of the item
            
        Returns:
            Dict: Item data or None if not found
        """
        try:
            result = self.supabase.table('items').select('*').eq('id', item_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error getting item by ID: {e}")
            return None
    
    def add_item(self, title: str, author: str, text: str, item_type: str = 'poem') -> Optional[str]:
        """Add a new item (poem or quote) to the database.
        
        Args:
            title: The title of the item
            author: The author of the item
            text: The text content of the item
            item_type: Type of item ('poem' or 'quote')
            
        Returns:
            str: The ID of the created item, or None if failed
        """
        try:
            # Generate semantic tags for the text
            structured_tags = self.tagger.analyze_poem(text, title, author)
            
            # Convert structured tags to array format for database storage
            tags_array = []
            for category, tag_list in structured_tags.items():
                if tag_list:  # Only add non-empty categories
                    tags_array.append(json.dumps({category: tag_list}))
            
            # Generate embedding for the text
            embedding = self.get_embedding(text)
            
            # Create the item data
            item_data = {
                'title': title,
                'author': author,
                'text': text,
                'type': item_type,
                'semantic_tags': tags_array,
                'embedding': embedding
            }
            
            # Insert into database
            result = self.supabase.table('items').insert(item_data).execute()
            
            if result.data and len(result.data) > 0:
                item_id = result.data[0]['id']
                print(f"Successfully added {item_type}: {title} by {author} (ID: {item_id})")
                return item_id
            else:
                print(f"Failed to add {item_type}: {title}")
                return None
                
        except Exception as e:
            print(f"Error adding item: {e}")
            return None
