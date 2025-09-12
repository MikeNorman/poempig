"""
Create proper database schema based on actual JSon poems.docx data structure
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
    """Create the poems table with schema based on actual data structure."""
    
    # SQL to create the poems table based on actual data structure
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS poems (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        type TEXT NOT NULL CHECK (type IN ('poem', 'quote')),
        author TEXT,
        text TEXT NOT NULL,
        name TEXT,
        tag TEXT,
        embedding VECTOR(1536), -- OpenAI text-embedding-3-small has 1536 dimensions
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create indexes for better performance
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_poems_type ON poems(type);",
        "CREATE INDEX IF NOT EXISTS idx_poems_author ON poems(author);",
        "CREATE INDEX IF NOT EXISTS idx_poems_name ON poems(name);",
        "CREATE INDEX IF NOT EXISTS idx_poems_tag ON poems(tag);",
        "CREATE INDEX IF NOT EXISTS idx_poems_embedding ON poems USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
    ]
    
    try:
        print("Creating poems table with proper schema...")
        result = sb.rpc('exec_sql', {'sql': create_table_sql}).execute()
        print("✅ Poems table created successfully")
        
        print("Creating indexes...")
        for index_sql in create_indexes_sql:
            try:
                sb.rpc('exec_sql', {'sql': index_sql}).execute()
                print(f"✅ Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                print(f"⚠️  Index creation failed (this is OK if pgvector is not installed): {e}")
        
        print("\n🎉 Database setup completed successfully!")
        print("Schema includes: id, type, author, text, name, tag, embedding, created_at, updated_at")
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        print("\nPlease create the table manually in your Supabase dashboard with the following SQL:")
        print("\n" + "="*50)
        print(create_table_sql)
        print("="*50)

if __name__ == "__main__":
    print("🔧 Creating proper database schema for Poem Recommender...")
    print(f"📡 Connecting to Supabase: {SUPABASE_URL}")
    create_poems_table()
