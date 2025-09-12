"""
Check if tag column exists in poems table
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

def check_tag_column():
    """Check if tag column exists by trying to insert a test record with tag."""
    
    try:
        print("Testing if tag column exists...")
        
        # Try to insert a test record with tag column
        test_record = {
            "title": "Test Title",
            "author": "Test Author", 
            "text": "Test poem content",
            "tag": "test,poem"
        }
        
        try:
            result = sb.table('poems').insert(test_record).execute()
            print("✅ Tag column exists and works!")
            print("📋 Current table structure supports: title, author, text, tag")
            
            # Show the inserted record
            if result.data:
                print("📄 Inserted test record:")
                for key, value in result.data[0].items():
                    print(f"  - {key}: {value}")
                
                # Clean up test record
                test_id = result.data[0]['id']
                sb.table('poems').delete().eq('id', test_id).execute()
                print("🧹 Test record cleaned up")
                
        except Exception as e:
            print(f"❌ Tag column doesn't exist or has issues: {e}")
            
            # Try without tag column
            test_record_no_tag = {
                "title": "Test Title",
                "author": "Test Author", 
                "text": "Test poem content"
            }
            
            try:
                result = sb.table('poems').insert(test_record_no_tag).execute()
                print("✅ Table works without tag column")
                print("📋 Current table structure: title, author, text")
                
                # Clean up
                if result.data:
                    test_id = result.data[0]['id']
                    sb.table('poems').delete().eq('id', test_id).execute()
                    print("🧹 Test record cleaned up")
                    
            except Exception as e2:
                print(f"❌ Table has issues: {e2}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Checking if tag column exists...")
    check_tag_column()
