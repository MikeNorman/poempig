"""
Check the actual schema of the poems table in Supabase
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

def check_schema():
    """Check what columns exist in the poems table."""
    try:
        # Try to get a sample record to see the schema
        result = sb.table('poems').select('*').limit(1).execute()
        print("✅ Successfully connected to poems table")
        print(f"📊 Found {len(result.data)} records")
        
        if result.data:
            print("\n📋 Table schema (from sample record):")
            for key, value in result.data[0].items():
                print(f"  - {key}: {type(value).__name__}")
        else:
            print("📋 Table is empty, checking structure...")
            # Try to insert a test record to see what columns are expected
            test_record = {
                "title": "Test",
                "author": "Test Author", 
                "text": "Test poem content",
                "kind": "poem"
            }
            try:
                insert_result = sb.table('poems').insert(test_record).execute()
                print("✅ Test record inserted successfully")
                print("📋 Available columns based on successful insert:")
                for key in test_record.keys():
                    print(f"  - {key}")
                # Clean up test record
                if insert_result.data:
                    test_id = insert_result.data[0]['id']
                    sb.table('poems').delete().eq('id', test_id).execute()
                    print("🧹 Test record cleaned up")
            except Exception as e:
                print(f"❌ Error inserting test record: {e}")
                
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == "__main__":
    print("🔍 Checking poems table schema...")
    check_schema()
