"""
Create vibe_profile_items junction table for linking vibe profiles to items.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
    raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env file")

# Initialize Supabase client
sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def create_vibe_profile_items_table():
    """Create the vibe_profile_items junction table."""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS vibe_profile_items (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        vibe_profile_id UUID NOT NULL REFERENCES vibe_profiles(id) ON DELETE CASCADE,
        item_id UUID NOT NULL REFERENCES poems(id) ON DELETE CASCADE,
        similarity_score FLOAT,
        assigned_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(vibe_profile_id, item_id)
    );
    """
    
    # Create indexes for performance
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_vibe_profile_items_profile ON vibe_profile_items(vibe_profile_id);",
        "CREATE INDEX IF NOT EXISTS idx_vibe_profile_items_item ON vibe_profile_items(item_id);",
        "CREATE INDEX IF NOT EXISTS idx_vibe_profile_items_similarity ON vibe_profile_items(similarity_score);"
    ]
    
    try:
        print("Creating vibe_profile_items table...")
        result = sb.rpc('exec_sql', {'sql': create_table_sql}).execute()
        print("✅ vibe_profile_items table created successfully")
        
        print("Creating indexes...")
        for index_sql in create_indexes_sql:
            sb.rpc('exec_sql', {'sql': index_sql}).execute()
        print("✅ Indexes created successfully")
        
        print("\n🎉 Vibe profile items table setup completed!")
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        print("\nPlease create the table manually in your Supabase dashboard with the following SQL:")
        print("\n" + "="*50)
        print(create_table_sql)
        print("="*50)
        for index_sql in create_indexes_sql:
            print(index_sql)
        print("="*50)

if __name__ == "__main__":
    print("🔧 Setting up vibe_profile_items table...")
    create_vibe_profile_items_table()
