#!/usr/bin/env python3
"""
Migrate to simplified vibe profile schema.
Adds seed_item_ids JSON column to vibe_profiles table.
"""

from supabase import create_client
import os
import json
from dotenv import load_dotenv

load_dotenv()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

def add_seed_item_ids_column():
    """Add seed_item_ids JSON column to vibe_profiles table"""
    print("🔄 Adding seed_item_ids column to vibe_profiles table...")
    
    try:
        # This would be done via SQL migration, but for now we'll just document it
        print("📝 SQL to run:")
        print("ALTER TABLE vibe_profiles ADD COLUMN seed_item_ids JSONB DEFAULT '[]'::jsonb;")
        print("✅ Column addition documented")
        return True
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        return False

def migrate_existing_data():
    """Migrate any existing junction table data to the new column"""
    print("🔄 Checking for existing junction table data...")
    
    try:
        # Check if junction table has any data
        junction_data = sb.table('vibe_profile_items').select('*').execute()
        
        if not junction_data.data:
            print("✅ No junction table data to migrate")
            return True
        
        print(f"📊 Found {len(junction_data.data)} junction records to migrate")
        
        # Group by vibe_profile_id
        profile_items = {}
        for record in junction_data.data:
            profile_id = record['vibe_profile_id']
            item_id = record['item_id']
            
            if profile_id not in profile_items:
                profile_items[profile_id] = []
            profile_items[profile_id].append(item_id)
        
        # Update each vibe profile with its item IDs
        for profile_id, item_ids in profile_items.items():
            try:
                sb.table('vibe_profiles').update({
                    'seed_item_ids': item_ids,
                    'seed_count': len(item_ids)
                }).eq('id', profile_id).execute()
                print(f"✅ Updated profile {profile_id} with {len(item_ids)} items")
            except Exception as e:
                print(f"❌ Error updating profile {profile_id}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error migrating data: {e}")
        return False

def drop_junction_table():
    """Drop the vibe_profile_items junction table"""
    print("🗑️ Dropping vibe_profile_items junction table...")
    
    try:
        # This would be done via SQL migration
        print("📝 SQL to run:")
        print("DROP TABLE IF EXISTS vibe_profile_items;")
        print("✅ Junction table drop documented")
        return True
    except Exception as e:
        print(f"❌ Error dropping table: {e}")
        return False

def main():
    print("🚀 Migrating to Simplified Vibe Profile Schema")
    print("=" * 50)
    
    # Step 1: Add the new column
    if not add_seed_item_ids_column():
        return
    
    # Step 2: Migrate existing data (if any)
    if not migrate_existing_data():
        return
    
    # Step 3: Drop the junction table
    if not drop_junction_table():
        return
    
    print("\n✅ Migration plan complete!")
    print("\n📋 Next steps:")
    print("1. Run the SQL commands shown above")
    print("2. Update your code to use seed_item_ids instead of junction table")
    print("3. Test the new schema")
    print("4. Update backup scripts to exclude vibe_profile_items table")

if __name__ == "__main__":
    main()
