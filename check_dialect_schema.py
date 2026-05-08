#!/usr/bin/env python3
"""Check dialect-related tables and columns"""

import sys
sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager

db_config = DatabaseConfigManager()
db_manager = DatabaseManager(db_config)
db_manager.current_db = 'AG_Dev'

# Check for dialect-related tables
tables_query = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND (table_name ILIKE '%dialect%' OR table_name ILIKE '%variant%' OR table_name ILIKE '%sub_language%')
ORDER BY table_name
"""

print("📊 Dialect-related tables:")
try:
    df = db_manager.execute_query(tables_query)
    if not df.empty:
        for table in df['table_name']:
            print(f"  - {table}")
            
            # Get columns for each table
            cols_query = f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
            """
            cols_df = db_manager.execute_query(cols_query)
            if not cols_df.empty:
                print(f"    Columns: {', '.join(cols_df['column_name'].tolist())}")
    else:
        print("  No dialect-specific tables found")
except Exception as e:
    print(f"  Error: {e}")

# Check languages table for dialect fields
print("\n📊 Languages table structure (dialect-related columns):")
lang_query = """
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'languages'
ORDER BY ordinal_position
"""
try:
    df = db_manager.execute_query(lang_query)
    if not df.empty:
        dialect_cols = [c for c in df['column_name'].tolist() 
                       if any(x in c.lower() for x in ['dialect', 'variant', 'sub'])]
        if dialect_cols:
            print(f"  Dialect-related columns: {', '.join(dialect_cols)}")
        else:
            print("  No dialect-specific columns in languages table")
except Exception as e:
    print(f"  Error: {e}")

# Check projects table for dialect_id
print("\n📊 Projects table structure:")
proj_query = """
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'projects'
ORDER BY ordinal_position
"""
try:
    df = db_manager.execute_query(proj_query)
    if not df.empty:
        dialect_cols = [c for c in df['column_name'].tolist() 
                       if any(x in c.lower() for x in ['dialect', 'variant', 'sub'])]
        if dialect_cols:
            print(f"  Dialect-related columns: {', '.join(dialect_cols)}")
        else:
            print("  No dialect-specific columns in projects table")
except Exception as e:
    print(f"  Error: {e}")
