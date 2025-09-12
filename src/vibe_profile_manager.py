"""
Simple Vibe Profile Manager for assigning items to vibe profiles.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

class VibeProfileManager:
    """Simple manager for vibe profile item assignments."""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase = create_client(self.supabase_url, self.supabase_key)
    
    def assign_item_to_vibe_profile(self, item_id: str, vibe_profile_id: str, similarity_score: float = None) -> bool:
        """Assign an item to a vibe profile."""
        try:
            # Check if the item is already assigned to this vibe profile
            existing = self.supabase.table('vibe_profile_items').select('*').eq('vibe_profile_id', vibe_profile_id).eq('item_id', item_id).execute()
            
            if existing.data:
                print(f"Item {item_id} is already assigned to vibe profile {vibe_profile_id}")
                return True  # Already exists, consider it successful
            
            # Insert the relationship
            result = self.supabase.table('vibe_profile_items').insert({
                'vibe_profile_id': vibe_profile_id,
                'item_id': item_id,
                'similarity_score': similarity_score
            }).execute()
            
            if result.data:
                # Update the size field
                self._update_vibe_profile_size(vibe_profile_id)
                # Update the vector
                self.update_vibe_profile_vector(vibe_profile_id)
                return True
            return False
            
        except Exception as e:
            print(f"Error assigning item to vibe profile: {e}")
            return False
    
    def remove_item_from_vibe_profile(self, item_id: str, vibe_profile_id: str) -> bool:
        """Remove an item from a vibe profile."""
        try:
            # Remove the relationship
            result = self.supabase.table('vibe_profile_items').delete().eq('item_id', item_id).eq('vibe_profile_id', vibe_profile_id).execute()
            
            if result.data:
                # Update the size field
                self._update_vibe_profile_size(vibe_profile_id)
                # Update the vector
                self.update_vibe_profile_vector(vibe_profile_id)
                return True
            return False
            
        except Exception as e:
            print(f"Error removing item from vibe profile: {e}")
            return False
    
    def get_items_for_vibe_profile(self, vibe_profile_id: str) -> List[Dict[str, Any]]:
        """Get all items for a vibe profile."""
        try:
            result = self.supabase.table('vibe_profile_items').select('*, poems(*)').eq('vibe_profile_id', vibe_profile_id).execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting items for vibe profile: {e}")
            return []
    
    def get_vibe_profiles_for_item(self, item_id: str) -> List[Dict[str, Any]]:
        """Get all vibe profiles for an item."""
        try:
            result = self.supabase.table('vibe_profile_items').select('*, vibe_profiles(*)').eq('item_id', item_id).execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting vibe profiles for item: {e}")
            return []
    
    def get_vibe_profile_stats(self) -> Dict[str, Any]:
        """Get basic stats about vibe profiles."""
        try:
            # Get all vibe profiles with their sizes
            profiles = self.supabase.table('vibe_profiles').select('id, name, size').execute()
            
            total_profiles = len(profiles.data) if profiles.data else 0
            total_items = sum(profile.get('size', 0) for profile in (profiles.data or []))
            
            return {
                'total_profiles': total_profiles,
                'total_items': total_items,
                'profiles': profiles.data or []
            }
        except Exception as e:
            print(f"Error getting vibe profile stats: {e}")
            return {'total_profiles': 0, 'total_items': 0, 'profiles': []}
    
    def _update_vibe_profile_size(self, vibe_profile_id: str):
        """Update the size field for a vibe profile."""
        try:
            # Count items for this vibe profile
            count_result = self.supabase.table('vibe_profile_items').select('id', count='exact').eq('vibe_profile_id', vibe_profile_id).execute()
            count = count_result.count or 0
            
            # Update the size field
            self.supabase.table('vibe_profiles').update({'size': count}).eq('id', vibe_profile_id).execute()
            
        except Exception as e:
            print(f"Error updating vibe profile size: {e}")
    
    def create_vibe_profile(self, name: str, poem_ids: List[str] = None) -> Optional[str]:
        """Create a new vibe profile."""
        try:
            # Check if a vibe profile with this name already exists
            existing = self.supabase.table('vibe_profiles').select('id').eq('name', name).execute()
            if existing.data:
                print(f"Vibe profile with name '{name}' already exists")
                return existing.data[0]['id']  # Return existing ID
            
            # If poem_ids are provided, check for content duplicates
            if poem_ids:
                # Check if there's already a vibe profile with the exact same set of poems
                existing_content = self._find_vibe_profile_with_poems(poem_ids)
                if existing_content:
                    print(f"Vibe profile with the same content already exists: {existing_content['name']}")
                    return existing_content['id']  # Return existing ID
            
            # Create a default empty vector (1536 dimensions of zeros)
            default_vector = [0.0] * 1536
            
            result = self.supabase.table('vibe_profiles').insert({
                'name': name,
                'vector': default_vector,
                'size': 0
            }).execute()
            
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            print(f"Error creating vibe profile: {e}")
            return None
    
    def _find_vibe_profile_with_poems(self, poem_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Find a vibe profile that contains exactly the same set of poems."""
        try:
            # Get all vibe profiles
            profiles_result = self.supabase.table('vibe_profiles').select('*').execute()
            
            if not profiles_result.data:
                return None
            
            # Sort the input poem_ids for comparison
            sorted_input_ids = sorted(poem_ids)
            
            for profile in profiles_result.data:
                # Get poems for this vibe profile
                poems = self.get_items_for_vibe_profile(profile['id'])
                profile_poem_ids = []
                
                for item in poems:
                    poem = item.get('poems')
                    if poem and poem.get('id'):
                        profile_poem_ids.append(poem['id'])
                
                # Sort and compare
                sorted_profile_ids = sorted(profile_poem_ids)
                
                if sorted_input_ids == sorted_profile_ids:
                    return {
                        'id': profile['id'],
                        'name': profile['name'],
                        'size': len(profile_poem_ids)
                    }
            
            return None
            
        except Exception as e:
            print(f"Error finding vibe profile with poems: {e}")
            return None
    
    def compute_vibe_profile_vector(self, vibe_profile_id: str) -> Optional[List[float]]:
        """Compute the centroid vector for a vibe profile based on its poems."""
        try:
            # Get all poems in this vibe profile
            items = self.get_items_for_vibe_profile(vibe_profile_id)
            
            if not items:
                return None
            
            # Extract embeddings
            embeddings = []
            for item in items:
                poem = item.get('poems')
                if poem and poem.get('embedding'):
                    if isinstance(poem['embedding'], str):
                        embedding = json.loads(poem['embedding'])
                    else:
                        embedding = poem['embedding']
                    embeddings.append(embedding)
            
            if not embeddings:
                return None
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings)
            
            # L2 normalize each embedding
            normalized_embeddings = embeddings_array / (np.linalg.norm(embeddings_array, axis=1, keepdims=True) + 1e-12)
            
            # Calculate centroid
            centroid = normalized_embeddings.mean(axis=0)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-12)  # L2 normalize centroid
            
            return centroid.tolist()
            
        except Exception as e:
            print(f"Error computing vibe profile vector: {e}")
            return None
    
    def update_vibe_profile_vector(self, vibe_profile_id: str) -> bool:
        """Update the centroid vector for a vibe profile."""
        try:
            vector = self.compute_vibe_profile_vector(vibe_profile_id)
            
            if vector is None:
                return False
            
            # Update the vibe profile with the new vector
            result = self.supabase.table('vibe_profiles').update({
                'vector': vector
            }).eq('id', vibe_profile_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error updating vibe profile vector: {e}")
            return False
    
    def update_vibe_profile_name(self, vibe_profile_id: str, name: str) -> bool:
        """Update the name of a vibe profile."""
        try:
            result = self.supabase.table('vibe_profiles').update({
                'name': name
            }).eq('id', vibe_profile_id).execute()
            
            return bool(result.data)
        except Exception as e:
            print(f"Error updating vibe profile name: {e}")
            return False
    
    def get_all_vibe_profiles_with_poems(self) -> List[Dict[str, Any]]:
        """Get all vibe profiles with their associated poems."""
        try:
            # Get all vibe profiles
            profiles_result = self.supabase.table('vibe_profiles').select('*').order('created_at', desc=True).execute()
            
            if not profiles_result.data:
                return []
            
            vibes = []
            for profile in profiles_result.data:
                # Get poems for this vibe profile
                poems = self.get_items_for_vibe_profile(profile['id'])
                poem_data = []
                
                for item in poems:
                    poem = item.get('poems')
                    if poem:
                        poem_data.append({
                            'id': poem['id'],
                            'title': poem.get('title', 'Untitled'),
                            'author': poem.get('author', 'Unknown'),
                            'text': poem.get('text', '')
                        })
                
                # Add the vibe profile once per profile, not per poem
                vibes.append({
                    'id': profile['id'],
                    'name': profile['name'],
                    'size': len(poem_data),
                    'created_at': profile.get('created_at'),
                    'poems': poem_data
                })
            
            return vibes
            
        except Exception as e:
            print(f"Error getting all vibe profiles with poems: {e}")
            return []
    
    def get_vibe_profile_with_poems(self, vibe_profile_id: str) -> Optional[Dict[str, Any]]:
        """Get a single vibe profile with its associated poems."""
        try:
            # Get the vibe profile
            profile_result = self.supabase.table('vibe_profiles').select('*').eq('id', vibe_profile_id).execute()
            
            if not profile_result.data:
                return None
            
            profile = profile_result.data[0]
            
            # Get poems for this vibe profile
            poems = self.get_items_for_vibe_profile(vibe_profile_id)
            poem_data = []
            
            for item in poems:
                poem = item.get('poems')
                if poem:
                    poem_data.append({
                        'id': poem['id'],
                        'title': poem.get('title', 'Untitled'),
                        'author': poem.get('author', 'Unknown'),
                        'text': poem.get('text', '')
                    })
            
            return {
                'id': profile['id'],
                'name': profile['name'],
                'size': len(poem_data),
                'created_at': profile.get('created_at'),
                'poems': poem_data
            }
            
        except Exception as e:
            print(f"Error getting vibe profile with poems: {e}")
            return None
    
    def find_similar_to_vibe_profile(self, vibe_profile_id: str, top_k: int = 5, exclude_poem_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Find poems similar to a vibe profile's vector, excluding poems already in the profile and additional exclusions."""
        try:
            # Get the vibe profile vector
            profile_result = self.supabase.table('vibe_profiles').select('vector').eq('id', vibe_profile_id).execute()
            vector = profile_result.data[0].get('vector') if profile_result.data else None
            
            if not vector:
                return []
            
            # Ensure vector is a numpy array of floats
            if isinstance(vector, str):
                vector = json.loads(vector)
            vector = np.array(vector, dtype=np.float32)
            
            # Get poems already in this vibe profile to exclude them
            existing_items_result = self.supabase.table('vibe_profile_items').select('item_id').eq('vibe_profile_id', vibe_profile_id).execute()
            existing_poem_ids = {item['item_id'] for item in (existing_items_result.data or [])}
            
            # Add additional poems to exclude (e.g., already displayed poems)
            if exclude_poem_ids:
                existing_poem_ids.update(exclude_poem_ids)
            
            # Use Supabase vector similarity search for accurate and fast results
            try:
                # Convert vector to the format Supabase expects
                # Ensure vector is a Python list, not numpy array
                if isinstance(vector, np.ndarray):
                    vector = vector.tolist()
                vector_str = json.dumps(vector)
                
                # Use Supabase's built-in vector similarity search
                poems_result = self.supabase.rpc('match_poems', {
                    'q': vector_str,  # Use 'q' parameter as expected by the function
                    'match_count': 50  # Get more than we need to account for exclusions
                }).execute()
                
                if not poems_result.data:
                    print("No results from vector search, falling back to manual calculation")
                    return self._manual_similarity_search(vector, existing_poem_ids, top_k)
                
                # Filter out poems that are already in the vibe profile or in the exclusion list
                available_poems = [poem for poem in poems_result.data if poem['id'] not in existing_poem_ids]
                
                if not available_poems:
                    print("No available poems after filtering, falling back to manual calculation")
                    return self._manual_similarity_search(vector, existing_poem_ids, top_k)
                
                # Convert to our expected format
                similarities = []
                for poem in available_poems:
                    similarities.append({
                        'poem': poem,
                        'similarity': float(poem.get('similarity', 0.0))
                    })
                
                # Sort by similarity and return top_k
                similarities.sort(key=lambda x: x['similarity'], reverse=True)
                return similarities[:top_k]
                
            except Exception as e:
                print(f"Vector search failed, falling back to manual calculation: {e}")
                # Fallback to the original method if vector search fails
                return self._manual_similarity_search(vector, existing_poem_ids, top_k)
            
        except Exception as e:
            print(f"Error finding similar to vibe profile: {e}")
            return []
    
    def _manual_similarity_search(self, vector, existing_poem_ids, top_k):
        """Fallback method for similarity search when vector search is not available."""
        try:
            # Get all poems with embeddings
            poems_result = self.supabase.table('poems').select('*').not_.is_('embedding', 'null').execute()
            
            if not poems_result.data:
                return []
            
            # Filter out poems that are already in the vibe profile or in the exclusion list
            available_poems = [poem for poem in poems_result.data if poem['id'] not in existing_poem_ids]
            
            if not available_poems:
                return []
            
            # Calculate similarities
            similarities = []
            for poem in available_poems:
                if poem.get('embedding'):
                    if isinstance(poem['embedding'], str):
                        poem_embedding = json.loads(poem['embedding'])
                    else:
                        poem_embedding = poem['embedding']
                    
                    # Ensure poem embedding is a numpy array of floats
                    poem_embedding = np.array(poem_embedding, dtype=np.float32)
                    
                    # Calculate cosine similarity
                    similarity = np.dot(vector, poem_embedding) / (
                        np.linalg.norm(vector) * np.linalg.norm(poem_embedding)
                    )
                    
                    similarities.append({
                        'poem': poem,
                        'similarity': float(similarity)  # Convert to Python float
                    })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Error in manual similarity search: {e}")
            return []
    
