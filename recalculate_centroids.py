#!/usr/bin/env python3
"""
Recalculate centroids for all vibe profiles using current embeddings
"""

import os
import numpy as np
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
    raise SystemExit("Missing environment variables")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def calculate_centroid(embeddings):
    """Calculate the centroid of a list of embeddings"""
    if not embeddings:
        return None
    
    # Convert to numpy array and calculate mean
    embeddings_array = np.array(embeddings)
    centroid = np.mean(embeddings_array, axis=0)
    return centroid.tolist()

def get_vibe_profile_seeds(profile_id):
    """Get all seed items for a vibe profile"""
    # Get items linked to this vibe profile through the seed_item_ids column
    try:
        # First get the vibe profile with its seed_item_ids
        profile_result = sb.table('vibe_profiles').select('seed_item_ids').eq('id', profile_id).execute()
        
        if not profile_result.data:
            return []
        
        item_ids = profile_result.data[0].get('seed_item_ids', [])
        
        if not item_ids:
            return []
        
        # Get the embeddings for these items
        items = sb.table('items').select('id,embedding').in_('id', item_ids).execute()
        
        if not items.data:
            return []
        
        # Filter out items without embeddings
        valid_embeddings = []
        for item in items.data:
            if item.get('embedding'):
                try:
                    # Parse embedding if it's a string
                    if isinstance(item['embedding'], str):
                        import json
                        embedding = json.loads(item['embedding'])
                    else:
                        embedding = item['embedding']
                    
                    if isinstance(embedding, list) and len(embedding) > 0:
                        valid_embeddings.append(embedding)
                except:
                    continue
        
        return valid_embeddings
        
    except Exception as e:
        print(f"    Error getting seeds for profile {profile_id}: {e}")
        return []

def recalculate_all_centroids():
    """Recalculate centroids for all vibe profiles"""
    
    print("🔄 Recalculating centroids for all vibe profiles...")
    
    # Get all vibe profiles
    profiles = sb.table('vibe_profiles').select('id,name').execute()
    
    if not profiles.data:
        print("❌ No vibe profiles found!")
        return
    
    print(f"📊 Found {len(profiles.data)} vibe profiles")
    
    updated_count = 0
    
    for profile in profiles.data:
        profile_id = profile['id']
        profile_name = profile['name']
        
        print(f"\n🎭 Processing: {profile_name}")
        
        # Get seed embeddings for this profile
        seed_embeddings = get_vibe_profile_seeds(profile_id)
        
        if not seed_embeddings:
            print(f"  ⚠️  No valid seed embeddings found for {profile_name}")
            continue
        
        print(f"  📝 Found {len(seed_embeddings)} seed embeddings")
        
        # Calculate new centroid
        new_centroid = calculate_centroid(seed_embeddings)
        
        if new_centroid is None:
            print(f"  ❌ Failed to calculate centroid for {profile_name}")
            continue
        
        # Update the profile with new centroid
        try:
            result = sb.table('vibe_profiles').update({
                'vector': new_centroid,
                'size': len(seed_embeddings)
            }).eq('id', profile_id).execute()
            
            print(f"  ✅ Updated centroid for {profile_name} (size: {len(seed_embeddings)})")
            updated_count += 1
            
        except Exception as e:
            print(f"  ❌ Error updating {profile_name}: {e}")
    
    print(f"\n✅ Centroid recalculation complete!")
    print(f"📊 Updated {updated_count}/{len(profiles.data)} vibe profiles")

def main():
    """Main function"""
    print("🚀 Recalculating Vibe Profile Centroids")
    print("=" * 50)
    
    recalculate_all_centroids()

if __name__ == "__main__":
    main()
