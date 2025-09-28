#!/usr/bin/env python3
"""
Complete database regeneration - clear all data and rebuild with fresh embeddings
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
    raise SystemExit("Missing environment variables")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def clear_database():
    """Clear all data from poems and vibe_profiles tables"""
    
    print("🗑️ Clearing database...")
    
    # Clear items table
    print("📝 Clearing items table...")
    try:
        items_response = sb.table('items').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print(f"✅ Cleared items table")
    except Exception as e:
        print(f"⚠️ Error clearing items: {e}")
    
    # Clear vibe_profiles table
    print("🎭 Clearing vibe_profiles table...")
    try:
        vibe_response = sb.table('vibe_profiles').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print(f"✅ Cleared vibe_profiles table")
    except Exception as e:
        print(f"⚠️ Error clearing vibe_profiles: {e}")
    
    print("✅ Database cleared!")

def main():
    """Run complete regeneration"""
    
    print("🚀 Starting Complete Database Regeneration")
    print("=" * 50)
    
    # Step 1: Create backup
    print("\n1️⃣ Creating backup...")
    from backup_database import backup_database
    backup_timestamp = backup_database()
    
    # Step 2: Clear database
    print("\n2️⃣ Clearing database...")
    clear_database()
    
    # Step 3: Ingest new poems
    print("\n3️⃣ Ingesting new poems...")
    print("Run: python scripts/ingest_complete.py scraped_poems.jsonl")
    
    # Step 4: Generate embeddings
    print("\n4️⃣ Generating embeddings...")
    print("Run: python scripts/generate_embeddings.py")
    
    print("\n✅ Complete regeneration setup complete!")
    print(f"📁 Backup saved with timestamp: {backup_timestamp}")
    print("\nNext steps:")
    print("1. Run: python scripts/ingest_complete.py scraped_poems.jsonl")
    print("2. Run: python scripts/generate_embeddings.py")

if __name__ == "__main__":
    main()
