"""
Semantic Tagger for Poems

This module analyzes poems and extracts semantic tags/themes for better search.
"""

import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class SemanticTagger:
    """Analyzes poems and extracts semantic tags for better search."""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def analyze_poem(self, poem_text: str, title: str = "", author: str = "") -> Dict[str, List[Dict[str, float]]]:
        """
        Analyze a poem and extract structured semantic tags with relevance scores.
        
        Args:
            poem_text (str): The poem text
            title (str): Poem title
            author (str): Poem author
            
        Returns:
            Dict[str, List[Dict[str, float]]]: Structured tags with relevance scores
        """
        try:
            # Skip if text is too short or empty
            if not poem_text or len(poem_text.strip()) < 10:
                return {"emotions": [], "themes": [], "imagery": [], "style": []}
            
            # Create a comprehensive prompt for structured semantic analysis
            prompt = f"""
            Analyze this poem and provide 8-12 semantic tags with relevance scores (0.0-1.0).
            
            Title: {title or 'Untitled'}
            Author: {author or 'Unknown'}
            Text: {poem_text[:500]}
            
            Categorize tags into:
            - emotions: feelings and emotional states (love, sadness, joy, anger, fear, hope, despair, etc.)
            - themes: universal concepts and subjects (death, nature, time, family, struggle, beauty, wisdom, etc.)
            - imagery: visual and sensory elements (light, darkness, water, fire, earth, sky, etc.)
            - style: tone and literary style (contemplative, narrative, lyrical, philosophical, etc.)
            
            For each tag, assign a relevance score:
            - 0.8-1.0: Core themes that strongly represent the content
            - 0.5-0.7: Important but secondary themes
            - 0.2-0.4: Present but not central
            
            Return ONLY a valid JSON object in this exact format:
            {{
                "emotions": [{{"tag": "love", "relevance": 0.9}}, {{"tag": "sadness", "relevance": 0.6}}],
                "themes": [{{"tag": "nature", "relevance": 0.8}}, {{"tag": "time", "relevance": 0.4}}],
                "imagery": [{{"tag": "light", "relevance": 0.7}}, {{"tag": "water", "relevance": 0.5}}],
                "style": [{{"tag": "contemplative", "relevance": 0.9}}, {{"tag": "lyrical", "relevance": 0.6}}]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert literary analyst specializing in poetry and literature. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Extract and parse JSON response
            if not response or not response.choices or not response.choices[0].message:
                return {"emotions": [], "themes": [], "imagery": [], "style": []}
            
            response_text = response.choices[0].message.content.strip()
            if not response_text:
                return {"emotions": [], "themes": [], "imagery": [], "style": []}
            
            # Clean up the response to ensure valid JSON
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            tags_data = json.loads(response_text)
            
            # Validate and clean the structure
            result = {
                "emotions": [],
                "themes": [],
                "imagery": [],
                "style": []
            }
            
            for category in result.keys():
                if category in tags_data and isinstance(tags_data[category], list):
                    for item in tags_data[category]:
                        if isinstance(item, dict) and "tag" in item and "relevance" in item:
                            tag = item["tag"].strip().lower()
                            relevance = float(item["relevance"])
                            if 0.0 <= relevance <= 1.0 and len(tag) > 1:
                                result[category].append({"tag": tag, "relevance": relevance})
            
            # Ensure we have at least some meaningful tags
            total_tags = sum(len(result[cat]) for cat in result.keys())
            if total_tags < 2:
                return {"emotions": [], "themes": [], "imagery": [], "style": []}
            
            return result
            
        except Exception as e:
            print(f"Error analyzing poem: {e}")
            import traceback
            traceback.print_exc()
            return {"emotions": [], "themes": [], "imagery": [], "style": []}
    
    def get_search_tags(self, query: str) -> List[str]:
        """
        Convert a search query into semantic tags for searching.
        
        Args:
            query (str): Search query
            
        Returns:
            List[str]: List of semantic tags to search for
        """
        try:
            prompt = f"""
            Convert this search query into 5-8 semantic tags that would help find relevant poems.
            
            Query: "{query}"
            
            Return only the tags as a comma-separated list. Focus on:
            - Emotional themes (love, sadness, joy, anger, fear, hope, etc.)
            - Life themes (nature, death, time, family, struggle, beauty, etc.)
            - Literary themes (memory, wisdom, truth, etc.)
            - Mood/tone (contemplative, lyrical, philosophical, etc.)
            
            Include synonyms and related terms for better search coverage.
            Examples: love, nature, grief, time, beauty, peace, struggle, hope, loss, growth
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3
            )
            
            # Extract tags from response
            tags_text = response.choices[0].message.content.strip()
            tags = [tag.strip().lower() for tag in tags_text.split(',') if tag.strip()]
            
            return tags[:10]  # Limit to 10 search tags
            
        except Exception as e:
            print(f"Error converting query to tags: {e}")
            return [query.lower()]  # Fallback to original query
