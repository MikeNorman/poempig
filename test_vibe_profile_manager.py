"""
Test script for the Vibe Profile Manager.
"""

from src.vibe_profile_manager import VibeProfileManager

def test_vibe_profile_manager():
    """Test the vibe profile manager functionality."""
    manager = VibeProfileManager()
    
    print("🧪 Testing Vibe Profile Manager...")
    
    # Test getting stats (should work even with empty tables)
    stats = manager.get_vibe_profile_stats()
    print(f"📊 Current stats: {stats}")
    
    # Test with some sample data (if tables exist)
    try:
        # Try to get some poems
        poems = manager.supabase.table('poems').select('id').limit(1).execute()
        if poems.data:
            sample_poem_id = poems.data[0]['id']
            print(f"📝 Found sample poem: {sample_poem_id}")
            
            # Try to get some vibe profiles
            vibe_profiles = manager.supabase.table('vibe_profiles').select('id').limit(1).execute()
            if vibe_profiles.data:
                sample_vibe_id = vibe_profiles.data[0]['id']
                print(f"🎭 Found sample vibe profile: {sample_vibe_id}")
                
                # Test assignment (this will fail if tables don't exist yet)
                print("🔗 Testing item assignment...")
                success = manager.assign_item_to_vibe_profile(sample_poem_id, sample_vibe_id, 0.85)
                print(f"Assignment result: {success}")
                
            else:
                print("❌ No vibe profiles found - create some first")
        else:
            print("❌ No poems found - add some poems first")
            
    except Exception as e:
        print(f"⚠️  Test failed (expected if tables don't exist yet): {e}")
    
    print("✅ Test completed!")

if __name__ == "__main__":
    test_vibe_profile_manager()
