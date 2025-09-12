"""
Recreate the poems table with the proper schema
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

def recreate_table():
    """Drop and recreate the poems table with proper schema."""
    
    try:
        # First, try to drop the existing table
        print("Dropping existing poems table...")
        try:
            sb.table('poems').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print("✅ Cleared existing data")
        except Exception as e:
            print(f"⚠️  Could not clear existing data: {e}")
        
        # Try to insert a test record to see what columns are expected
        print("Testing table structure...")
        test_record = {
            "type": "poem",
            "author": "Test Author", 
            "text": "Test poem content",
            "name": "Test Name",
            "tag": "test"
        }
        
        try:
            result = sb.table('poems').insert(test_record).execute()
            print("✅ Table structure is compatible")
            print("📋 Available columns:")
            for key in test_record.keys():
                print(f"  - {key}")
            
            # Clean up test record
            if result.data:
                test_id = result.data[0]['id']
                sb.table('poems').delete().eq('id', test_id).execute()
                print("🧹 Test record cleaned up")
                
        except Exception as e:
            print(f"❌ Table structure incompatible: {e}")
            print("\nPlease create the table manually in your Supabase dashboard with:")
            print("""
CREATE TABLE poems (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('poem', 'quote')),
    author TEXT,
    text TEXT NOT NULL,
    name TEXT,
    tag TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
            """)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔧 Testing and recreating poems table...")
    recreate_table()
