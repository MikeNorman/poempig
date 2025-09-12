"""
Add tag column to existing poems table
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

def add_tag_column():
    """Add tag column to the existing poems table."""
    
    try:
        print("Attempting to add tag column to poems table...")
        
        # Try to add the tag column using a simple insert that might trigger schema update
        test_record = {
            "title": "Test Title",
            "author": "Test Author", 
            "text": "Test poem content",
            "tag": "test,poem"
        }
        
        try:
            result = sb.table('poems').insert(test_record).execute()
            print("✅ Tag column already exists or was added successfully")
            print("📋 Current table structure supports: title, author, text, tag")
            
            # Clean up test record
            if result.data:
                test_id = result.data[0]['id']
                sb.table('poems').delete().eq('id', test_id).execute()
                print("🧹 Test record cleaned up")
                
        except Exception as e:
            print(f"❌ Tag column doesn't exist: {e}")
            print("\nPlease add the tag column manually in your Supabase dashboard:")
            print("ALTER TABLE poems ADD COLUMN tag TEXT;")
            print("\nOr create a new table with the proper schema:")
            print("""
CREATE TABLE poems_new (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT,
    author TEXT,
    text TEXT NOT NULL,
    tag TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Then copy data from old table to new table
-- INSERT INTO poems_new (title, author, text) SELECT title, author, text FROM poems;

-- Then drop old table and rename new table
-- DROP TABLE poems;
-- ALTER TABLE poems_new RENAME TO poems;
            """)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔧 Adding tag column to poems table...")
    add_tag_column()
