#!/usr/bin/env python3
"""
Export Database Schemas to Text Files
"""

import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager

OUTPUT_DIR = Path("./output/schema")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

db_config = DatabaseConfigManager()


def export_schema(db_name: str) -> str:
    """Export complete schema for a database"""
    
    output_file = OUTPUT_DIR / f"{db_name}_complete_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print(f"\n{'='*80}")
    print(f"Exporting schema for: {db_name}")
    print(f"Output file: {output_file}")
    print(f"{'='*80}")
    
    # Create a new database manager for each database
    db_manager = DatabaseManager(db_config)
    db_manager.current_db = db_name  # Set the current database
    
    with open(output_file, 'w') as f:
        f.write(f"DATABASE SCHEMA EXPORT\n")
        f.write(f"Database: {db_name}\n")
        f.write(f"Export Date: {datetime.now().isoformat()}\n")
        f.write(f"{'='*80}\n\n")
        
        # Get all tables
        try:
            tables = db_manager.get_all_tables(db_name)
            print(f"Found {len(tables)} tables")
            
            for idx, table_name in enumerate(tables, 1):
                print(f"  Processing: {table_name} ({idx}/{len(tables)})")
                
                f.write(f"\n{'='*60}\n")
                f.write(f"TABLE: {table_name}\n")
                f.write(f"{'='*60}\n\n")
                
                # Get column details
                try:
                    query = f"""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                    """
                    columns_df = db_manager.execute_query(query, db_name=db_name)
                    
                    if not columns_df.empty:
                        for _, col in columns_df.iterrows():
                            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                            f.write(f"  {col['column_name']}: {col['data_type']} ({nullable}){default}\n")
                    
                    # Get row count
                    row_count = db_manager.get_table_count(table_name, db_name)
                    f.write(f"\n  Row Count: {row_count:,}\n")
                    
                except Exception as e:
                    f.write(f"\n  ERROR: {e}\n")
                
                f.write("\n")
        except Exception as e:
            print(f"  Error getting tables: {e}")
            f.write(f"\nERROR: {e}\n")
    
    print(f"\n✅ Schema exported to: {output_file}")
    return str(output_file)


def main():
    print("\n" + "="*80)
    print("DATABASE SCHEMA EXPORTER")
    print("="*80)
    
    # Export both databases
    for db_name in ['AG_Dev', 'Telios_LMS_Dev']:
        try:
            export_schema(db_name)
        except Exception as e:
            print(f"\n⚠️ Could not export {db_name}: {e}")
    
    print("\n" + "="*80)
    print("EXPORT COMPLETE")
    print("="*80)
    print(f"\n📁 Schema files saved in: {OUTPUT_DIR}")
    print("\nYou can view them with:")
    print(f"  cat {OUTPUT_DIR}/AG_Dev_complete_schema_*.txt | head -100")
    print(f"  cat {OUTPUT_DIR}/Telios_LMS_Dev_complete_schema_*.txt | head -100")


if __name__ == '__main__':
    main()
