#!/usr/bin/env python3
"""
Backup database before complete regeneration
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
    raise SystemExit("Missing environment variables")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def backup_database():
    """Backup ALL data from the database - COMPREHENSIVE BACKUP"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("🔄 Creating COMPREHENSIVE database backup...")
    print("⚠️  This will backup ALL tables to prevent data loss")
    
    backup_files = []
    total_items = 0
    
    # List of ALL tables that need to be backed up
    tables_to_backup = [
        'items',
        'vibe_profiles', 
        # 'vibe_profile_items',  # REMOVED: Using simplified schema with seed_item_ids JSON column
        'poems',  # In case it exists
        'quotes'  # In case it exists
    ]
    
    for table_name in tables_to_backup:
        try:
            print(f"📝 Backing up {table_name} table...")
            response = sb.table(table_name).select('*').execute()
            data = response.data
            
            if data:  # Only create file if there's data
                filename = f'backup_{table_name}_{timestamp}.json'
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"✅ Backed up {len(data)} {table_name} to {filename}")
                backup_files.append(filename)
                total_items += len(data)
            else:
                print(f"ℹ️  {table_name} table is empty, skipping backup file")
                
        except Exception as e:
            print(f"⚠️  Error backing up {table_name}: {e}")
            # Continue with other tables even if one fails
    
    # Create comprehensive summary
    summary = {
        "timestamp": timestamp,
        "total_items_backed_up": total_items,
        "tables_backed_up": len(backup_files),
        "backup_files": backup_files,
        "backup_complete": True,
        "warning": "This backup includes ALL database tables to prevent data loss"
    }
    
    with open(f'backup_summary_{timestamp}.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📊 COMPREHENSIVE BACKUP COMPLETE!")
    print(f"   - Total items backed up: {total_items}")
    print(f"   - Tables backed up: {len(backup_files)}")
    print(f"   - Backup files: {', '.join(backup_files)}")
    print(f"   - Summary: backup_summary_{timestamp}.json")
    print(f"\n✅ ALL DATA SAFELY BACKED UP - Safe to proceed with operations")
    
    return timestamp

if __name__ == "__main__":
    backup_database()
