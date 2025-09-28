"""
Simple Vibe Profile Manager for assigning items to vibe profiles.
"""

import os
import json
import math
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
            # Get current vibe profile
            profile_result = self.supabase.table('vibe_profiles').select('seed_item_ids').eq('id', vibe_profile_id).execute()
            
            if not profile_result.data:
                print(f"Vibe profile {vibe_profile_id} not found")
                return False
            
            current_item_ids = profile_result.data[0].get('seed_item_ids', [])
            
            # Check if item is already assigned
            if item_id in current_item_ids:
                print(f"Item {item_id} is already assigned to vibe profile {vibe_profile_id}")
                return True  # Already exists, consider it successful
            
            # Add item to the list
            new_item_ids = current_item_ids + [item_id]
            
            # Update the vibe profile
            result = self.supabase.table('vibe_profiles').update({
                'seed_item_ids': new_item_ids,
                'size': len(new_item_ids)
            }).eq('id', vibe_profile_id).execute()
            
            if result.data:
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
            # Get current vibe profile
            profile_result = self.supabase.table('vibe_profiles').select('seed_item_ids').eq('id', vibe_profile_id).execute()
            
            if not profile_result.data:
                print(f"Vibe profile {vibe_profile_id} not found")
                return False
            
            current_item_ids = profile_result.data[0].get('seed_item_ids', [])
            
            # Remove item from the list
            if item_id in current_item_ids:
                new_item_ids = [id for id in current_item_ids if id != item_id]
                
                # Update the vibe profile
                result = self.supabase.table('vibe_profiles').update({
                    'seed_item_ids': new_item_ids,
                    'size': len(new_item_ids)
                }).eq('id', vibe_profile_id).execute()
                
                if result.data:
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
            # Get the vibe profile with its seed_item_ids
            profile_result = self.supabase.table('vibe_profiles').select('seed_item_ids').eq('id', vibe_profile_id).execute()
            
            if not profile_result.data:
                return []
            
            item_ids = profile_result.data[0].get('seed_item_ids', [])
            
            if not item_ids:
                return []
            
            # Get the items
            items_result = self.supabase.table('items').select('*').in_('id', item_ids).execute()
            
            # Format to match the old junction table structure
            formatted_items = []
            for item in (items_result.data or []):
                formatted_items.append({
                    'items': item,
                    'item_id': item['id'],
                    'vibe_profile_id': vibe_profile_id
                })
            
            return formatted_items
        except Exception as e:
            print(f"Error getting items for vibe profile: {e}")
            return []
    
    def get_vibe_profiles_for_item(self, item_id: str) -> List[Dict[str, Any]]:
        """Get all vibe profiles for an item."""
        try:
            # Get all vibe profiles and filter those that contain this item_id
            profiles_result = self.supabase.table('vibe_profiles').select('*').execute()
            
            # Filter profiles that contain this item_id in their seed_item_ids
            matching_profiles = []
            for profile in (profiles_result.data or []):
                seed_item_ids = profile.get('seed_item_ids', [])
                if item_id in seed_item_ids:
                    matching_profiles.append(profile)
            
            # Format to match the old junction table structure
            formatted_profiles = []
            for profile in matching_profiles:
                formatted_profiles.append({
                    'vibe_profiles': profile,
                    'item_id': item_id,
                    'vibe_profile_id': profile['id']
                })
            
            return formatted_profiles
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
            # Get the vibe profile with its seed_item_ids
            profile_result = self.supabase.table('vibe_profiles').select('seed_item_ids').eq('id', vibe_profile_id).execute()
            
            if profile_result.data:
                item_ids = profile_result.data[0].get('seed_item_ids', [])
                count = len(item_ids)
                
                # Update the size field
                self.supabase.table('vibe_profiles').update({'size': count}).eq('id', vibe_profile_id).execute()
            
        except Exception as e:
            print(f"Error updating vibe profile size: {e}")
    
    def create_vibe_profile(self, name: str, item_ids: List[str] = None) -> Optional[str]:
        """Create a new vibe profile."""
        try:
            # Check if a vibe profile with this name already exists
            existing = self.supabase.table('vibe_profiles').select('id').eq('name', name).execute()
            if existing.data:
                # Generate a unique name by adding a timestamp
                import time
                unique_name = f"{name} ({int(time.time())})"
                print(f"Vibe profile with name '{name}' already exists, using '{unique_name}'")
                name = unique_name
            
            # If item_ids are provided, check for content duplicates
            if item_ids:
                # Check if there's already a vibe profile with the exact same set of items
                existing_content = self._find_vibe_profile_with_items(item_ids)
                if existing_content:
                    print(f"Vibe profile with the same content already exists: {existing_content['name']}")
                    return existing_content['id']  # Return existing ID
            
            # Create a default empty vector (1536 dimensions of zeros)
            default_vector = [0.0] * 1536
            
            result = self.supabase.table('vibe_profiles').insert({
                'name': name,
                'vector': default_vector,
                'size': 0,
                'seed_item_ids': []
            }).execute()
            
            if result.data:
                vibe_profile_id = result.data[0]['id']
                
                # Add items to the vibe profile if provided
                if item_ids:
                    for item_id in item_ids:
                        self.assign_item_to_vibe_profile(item_id, vibe_profile_id)
                
                return vibe_profile_id
            return None
        except Exception as e:
            print(f"Error creating vibe profile: {e}")
            return None
    
    def _find_vibe_profile_with_items(self, item_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Find a vibe profile that contains exactly the same set of poems."""
        try:
            # Get all vibe profiles
            profiles_result = self.supabase.table('vibe_profiles').select('*').execute()
            
            if not profiles_result.data:
                return None
            
            # Sort the input item_ids for comparison
            sorted_input_ids = sorted(item_ids)
            
            for profile in profiles_result.data:
                # Get items for this vibe profile
                items = self.get_items_for_vibe_profile(profile['id'])
                profile_item_ids = []
                
                for item in items:
                    item_data = item.get('items')
                    if item_data and item_data.get('id'):
                        profile_item_ids.append(item_data['id'])
                
                # Sort and compare
                sorted_profile_ids = sorted(profile_item_ids)
                
                if sorted_input_ids == sorted_profile_ids:
                    return {
                        'id': profile['id'],
                        'name': profile['name'],
                        'size': len(profile_item_ids)
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
                poem = item.get('items')
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
                    poem = item.get('items')
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
                poem = item.get('items')
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
    
    def find_similar_to_vibe_profile(self, vibe_profile_id: str, top_k: int = 5, exclude_item_ids: List[str] = None) -> List[Dict[str, Any]]:
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
            profile_result = self.supabase.table('vibe_profiles').select('seed_item_ids').eq('id', vibe_profile_id).execute()
            existing_item_ids = set(profile_result.data[0].get('seed_item_ids', []) if profile_result.data else [])
            
            # Add additional items to exclude (e.g., already displayed items)
            if exclude_item_ids:
                existing_item_ids.update(exclude_item_ids)
            
            # Use Supabase vector similarity search for accurate and fast results
            try:
                # Convert vector to the format Supabase expects
                # Ensure vector is a Python list, not numpy array
                if isinstance(vector, np.ndarray):
                    vector = vector.tolist()
                vector_str = json.dumps(vector)
                
                # Use Supabase's built-in vector similarity search
                print(f"VIBE PROFILE DEBUG: Calling match_items with vector_str length: {len(vector_str)}")
                print(f"VIBE PROFILE DEBUG: Vector preview: {vector_str[:100]}...")
                
                poems_result = self.supabase.rpc('match_items', {
                    'q': vector_str,  # Use 'q' parameter as expected by the deployed function
                    'match_count': 50  # Get more than we need to account for exclusions
                }).execute()
                
                print(f"VIBE PROFILE DEBUG: Raw result from Supabase: {poems_result}")
                print(f"VIBE PROFILE DEBUG: Result data type: {type(poems_result.data)}")
                print(f"VIBE PROFILE DEBUG: Result data length: {len(poems_result.data) if poems_result.data else 0}")
                
                if not poems_result.data:
                    print("No results from vector search, falling back to manual calculation")
                    return self._manual_similarity_search(vector, existing_item_ids, top_k)
                
                # Filter out poems that are already in the vibe profile or in the exclusion list
                available_poems = [poem for poem in poems_result.data if poem['id'] not in existing_item_ids]
                
                if not available_poems:
                    print("No available poems after filtering, falling back to manual calculation")
                    return self._manual_similarity_search(vector, existing_item_ids, top_k)
                
                # Convert to our expected format
                similarities = []
                for poem in available_poems:
                    similarity = poem.get('similarity', 0.0)
                    # Ensure similarity is a valid number
                    if similarity is None:
                        similarity = 0.0
                    else:
                        try:
                            similarity = float(similarity)
                            if math.isnan(similarity) or math.isinf(similarity):
                                similarity = 0.0
                        except (ValueError, TypeError):
                            similarity = 0.0
                    
                    similarities.append({
                        'item': poem,
                        'similarity': similarity
                    })
                
                # Sort by similarity and return top_k
                similarities.sort(key=lambda x: x['similarity'], reverse=True)
                return similarities[:top_k]
                
            except Exception as e:
                print(f"Vector search failed, falling back to manual calculation: {e}")
                # Fallback to the original method if vector search fails
                return self._manual_similarity_search(vector, existing_item_ids, top_k)
            
        except Exception as e:
            print(f"Error finding similar to vibe profile: {e}")
            return []
    
    def _manual_similarity_search(self, vector, existing_item_ids, top_k):
        """Fallback method for similarity search when vector search is not available."""
        try:
            # Get all poems with embeddings
            poems_result = self.supabase.table('items').select('*').not_.is_('embedding', 'null').execute()
            
            if not poems_result.data:
                return []
            
            # Filter out items that are already in the vibe profile or in the exclusion list
            available_poems = [poem for poem in poems_result.data if poem['id'] not in existing_item_ids]
            
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
                    vector_norm = np.linalg.norm(vector)
                    poem_norm = np.linalg.norm(poem_embedding)
                    
                    # Avoid division by zero and NaN values
                    if vector_norm == 0 or poem_norm == 0:
                        similarity = 0.0
                    else:
                        similarity = np.dot(vector, poem_embedding) / (vector_norm * poem_norm)
                        # Ensure similarity is a valid number
                        similarity = float(similarity)
                        if math.isnan(similarity) or math.isinf(similarity):
                            similarity = 0.0
                    
                    similarities.append({
                        'item': poem,
                        'similarity': float(similarity)  # Convert to Python float
                    })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Error in manual similarity search: {e}")
            return []
    
    def delete_vibe_profile(self, vibe_profile_id: str) -> bool:
        """Delete a vibe profile and all its associated items."""
        try:
            # Delete the vibe profile (seed_item_ids will be automatically cleaned up)
            delete_vibe_result = self.supabase.table('vibe_profiles').delete().eq('id', vibe_profile_id).execute()
            
            if delete_vibe_result.data:
                print(f"Successfully deleted vibe profile {vibe_profile_id}")
                return True
            else:
                print(f"Failed to delete vibe profile {vibe_profile_id}")
                return False
                
        except Exception as e:
            print(f"Error deleting vibe profile {vibe_profile_id}: {e}")
            return False
    
    def cleanup_vibe_profiles_with_few_items(self, min_items=2):
        """Delete vibe profiles that have fewer than the specified minimum number of items."""
        try:
            # Get all vibe profiles with their item counts
            profiles_result = self.supabase.table('vibe_profiles').select('id, name, size').execute()
            
            if not profiles_result.data:
                print("No vibe profiles found")
                return
            
            profiles_to_delete = []
            
            for profile in profiles_result.data:
                item_count = profile.get('size', 0)
                if item_count < min_items:
                    profiles_to_delete.append({
                        'id': profile['id'],
                        'name': profile['name'],
                        'item_count': item_count
                    })
            
            if not profiles_to_delete:
                print(f"All vibe profiles have {min_items} or more items. No cleanup needed.")
                return
            
            print(f"Found {len(profiles_to_delete)} vibe profiles with fewer than {min_items} items:")
            for profile in profiles_to_delete:
                print(f"  - {profile['name']} (ID: {profile['id']}) - {profile['item_count']} items")
            
            # Ask for confirmation
            response = input(f"\nDelete these {len(profiles_to_delete)} vibe profiles? (y/N): ")
            if response.lower() != 'y':
                print("Cleanup cancelled.")
                return
            
            # Delete the profiles
            deleted_count = 0
            for profile in profiles_to_delete:
                if self.delete_vibe_profile(profile['id']):
                    deleted_count += 1
                    print(f"✅ Deleted: {profile['name']}")
                else:
                    print(f"❌ Failed to delete: {profile['name']}")
            
            print(f"\nCleanup complete. Deleted {deleted_count} out of {len(profiles_to_delete)} vibe profiles.")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == '__main__':
    # Run cleanup when script is executed directly
    import sys
    
    # Load environment variables
    load_dotenv()
    
    # Initialize vibe profile manager
    vibe_manager = VibeProfileManager()
    
    # Get minimum items from command line argument or use default
    min_items = 2
    if len(sys.argv) > 1:
        try:
            min_items = int(sys.argv[1])
        except ValueError:
            print("Invalid minimum items value. Using default of 2.")
    
    print(f"🧹 Starting cleanup of vibe profiles with fewer than {min_items} items...")
    vibe_manager.cleanup_vibe_profiles_with_few_items(min_items)
    
