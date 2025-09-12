"""
Check what columns actually exist in the poems table
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
    """Check what columns actually exist in the poems table."""
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
            print("📋 Table is empty, trying to determine structure...")
            # Try different column combinations
            test_columns = [
                ["title", "author", "text"],
                ["author", "text"],
                ["text"],
                ["title", "text", "author", "type"],
                ["id", "title", "author", "text"]
            ]
            
            for columns in test_columns:
                try:
                    result = sb.table('poems').select(','.join(columns)).limit(1).execute()
                    print(f"✅ Found columns: {columns}")
                    break
                except Exception as e:
                    print(f"❌ Columns {columns} not found: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == "__main__":
    print("🔍 Checking actual poems table schema...")
    check_schema()
