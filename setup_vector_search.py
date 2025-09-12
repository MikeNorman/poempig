#!/usr/bin/env python3
"""
Setup vector search for Supabase
This script sets up pgvector extension and creates the necessary functions for vector similarity search.
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def setup_vector_search():
    """Set up vector search in Supabase."""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Read the SQL file
        with open('setup_vector_search.sql', 'r') as f:
            sql_commands = f.read()
        
        # Split by semicolon and execute each command
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
        
        for i, command in enumerate(commands):
            print(f"Executing command {i+1}/{len(commands)}...")
            try:
                result = supabase.rpc('exec_sql', {'sql': command}).execute()
                print(f"✅ Command {i+1} executed successfully")
            except Exception as e:
                print(f"⚠️  Command {i+1} failed: {e}")
                # Continue with other commands
        
        print("\n🎉 Vector search setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up vector search: {e}")
        return False

if __name__ == "__main__":
    setup_vector_search()
