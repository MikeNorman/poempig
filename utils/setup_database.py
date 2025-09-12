"""
Database Setup Script for Poem Recommender

This script creates the necessary Supabase table for storing poems.
Run this before ingesting any poems.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
    raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env file")

# Initialize Supabase client
sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def create_poems_table():
    """Create the poems table with the required schema."""
    
    # SQL to create the poems table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS poems (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        content_hash TEXT UNIQUE NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN ('poem', 'quote')),
        title TEXT,
        author TEXT,
        text TEXT NOT NULL,
        lang TEXT DEFAULT 'und',
        lines_count INTEGER DEFAULT 0,
        tags JSONB DEFAULT '{"themes": [], "tone": [], "form": [], "devices": []}',
        embedding VECTOR(1536), -- OpenAI text-embedding-3-small has 1536 dimensions
        source TEXT DEFAULT 'unknown',
        visibility TEXT DEFAULT 'private' CHECK (visibility IN ('public', 'private')),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create index for content_hash for faster lookups
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_poems_content_hash ON poems(content_hash);
    """
    
    # Create index for author for faster author-based queries
    create_author_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_poems_author ON poems(author);
    """
    
    # Create index for kind for filtering
    create_kind_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_poems_kind ON poems(kind);
    """
    
    # Create index for embedding for similarity search (if using pgvector)
    create_embedding_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_poems_embedding ON poems USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    """
    
    try:
        print("Creating poems table...")
        result = sb.rpc('exec_sql', {'sql': create_table_sql}).execute()
        print("✅ Poems table created successfully")
        
        print("Creating indexes...")
        sb.rpc('exec_sql', {'sql': create_index_sql}).execute()
        sb.rpc('exec_sql', {'sql': create_author_index_sql}).execute()
        sb.rpc('exec_sql', {'sql': create_kind_index_sql}).execute()
        print("✅ Indexes created successfully")
        
        # Note: The embedding index requires pgvector extension
        # This might fail if pgvector is not installed in your Supabase instance
        try:
            sb.rpc('exec_sql', {'sql': create_embedding_index_sql}).execute()
            print("✅ Embedding index created successfully")
        except Exception as e:
            print(f"⚠️  Embedding index creation failed (this is OK if pgvector is not installed): {e}")
        
        print("\n🎉 Database setup completed successfully!")
        print("You can now run the ingestion script to add poems to the database.")
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        print("\nTrying alternative approach...")
        
        # Alternative: Try to create table using direct SQL execution
        try:
            # This might work if the RPC function doesn't exist
            print("Attempting to create table using direct SQL...")
            # Note: This approach might not work depending on your Supabase setup
            print("Please create the table manually in your Supabase dashboard with the following SQL:")
            print("\n" + "="*50)
            print(create_table_sql)
            print("="*50)
            print("\nThen run the ingestion script again.")
            
        except Exception as e2:
            print(f"❌ Alternative approach also failed: {e2}")
            print("\nPlease create the table manually in your Supabase dashboard.")

def check_table_exists():
    """Check if the poems table already exists."""
    try:
        result = sb.table('poems').select('id').limit(1).execute()
        print("✅ Poems table already exists")
        return True
    except Exception as e:
        print(f"❌ Poems table does not exist: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Setting up database for Poem Recommender...")
    print(f"📡 Connecting to Supabase: {SUPABASE_URL}")
    
    if not check_table_exists():
        create_poems_table()
    else:
        print("✅ Database is already set up!")
