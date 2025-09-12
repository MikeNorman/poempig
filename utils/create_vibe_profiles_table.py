"""
Create vibe_profiles table with vector field for centroid.
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

def create_vibe_profiles_table():
    """Create the vibe_profiles table with vector field for centroid."""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS vibe_profiles (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        name TEXT NOT NULL,
        centroid VECTOR(1536), -- OpenAI text-embedding-3-small has 1536 dimensions
        size INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create indexes for performance
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_vibe_profiles_name ON vibe_profiles(name);",
        "CREATE INDEX IF NOT EXISTS idx_vibe_profiles_size ON vibe_profiles(size);",
        "CREATE INDEX IF NOT EXISTS idx_vibe_profiles_centroid ON vibe_profiles USING ivfflat (centroid vector_cosine_ops) WITH (lists = 100);"
    ]
    
    try:
        print("Creating vibe_profiles table...")
        result = sb.rpc('exec_sql', {'sql': create_table_sql}).execute()
        print("✅ vibe_profiles table created successfully")
        
        print("Creating indexes...")
        for index_sql in create_indexes_sql:
            sb.rpc('exec_sql', {'sql': index_sql}).execute()
        print("✅ Indexes created successfully")
        
        print("\n🎉 Vibe profiles table setup completed!")
        
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
    print("🔧 Setting up vibe_profiles table...")
    create_vibe_profiles_table()
