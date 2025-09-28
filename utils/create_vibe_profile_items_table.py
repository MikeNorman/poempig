"""
DEPRECATED: This file is no longer needed with the simplified schema.
We now use seed_item_ids JSON column in vibe_profiles table instead of a junction table.

This file is kept for reference but should not be used.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def create_vibe_profile_items_table():
    """DEPRECATED: Junction table no longer needed with simplified schema."""
    print("⚠️  WARNING: This function is deprecated!")
    print("   The vibe_profile_items junction table is no longer needed.")
    print("   We now use seed_item_ids JSON column in vibe_profiles table.")
    print("   This provides better performance and simpler data management.")
    return

if __name__ == "__main__":
    print("⚠️  DEPRECATED: vibe_profile_items junction table is no longer needed")
    print("   The application now uses a simplified schema with seed_item_ids JSON column.")
    print("   This file is kept for reference but should not be used.")
    print("   See simplify_vibe_profiles_schema.sql for the new schema.")
    create_vibe_profile_items_table()