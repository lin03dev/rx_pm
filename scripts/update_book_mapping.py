#!/usr/bin/env python3
"""
Update Book Mapping Configuration
Utility to discover and update book ID mappings
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.book_mapping_config import BookMappingConfig
from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager

def discover_assigned_books(db_name: str = "AG_Dev"):
    """Discover all unique assigned book numbers from users_to_projects"""
    db_config = DatabaseConfigManager()
    db_manager = DatabaseManager(db_config)
    
    query = """
    SELECT DISTINCT SUBSTRING(verse_id FROM 1 FOR 3) as book_prefix
    FROM users_to_projects utp
    CROSS JOIN LATERAL unnest(string_to_array(COALESCE(utp.verses, ''), ',')) AS verse_id
    WHERE utp.verses IS NOT NULL AND utp.verses != '' AND verse_id != ''
    ORDER BY book_prefix
    """
    
    try:
        df = db_manager.execute_query(query, db_name=db_name)
        assigned_books = sorted([int(row['book_prefix']) for _, row in df.iterrows()])
        print(f"Found assigned book numbers: {assigned_books}")
        return assigned_books
    except Exception as e:
        print(f"Error discovering assigned books: {e}")
        return []


def discover_translated_books(db_name: str = "AG_Dev"):
    """Discover all unique translated book numbers from text_translation_chapters"""
    db_config = DatabaseConfigManager()
    db_manager = DatabaseManager(db_config)
    
    query = """
    SELECT DISTINCT ttb."bookNo"
    FROM text_translation_chapters ttc
    LEFT JOIN text_translation_books ttb ON ttc."textTranslationBookId" = ttb.id
    WHERE ttb."bookNo" IS NOT NULL
    ORDER BY ttb."bookNo"
    """
    
    try:
        df = db_manager.execute_query(query, db_name=db_name)
        translated_books = sorted([int(row['bookNo']) for _, row in df.iterrows()])
        print(f"Found translated book numbers: {translated_books}")
        return translated_books
    except Exception as e:
        print(f"Error discovering translated books: {e}")
        return []


def suggest_mappings(assigned_books, translated_books):
    """Suggest mapping rules based on discovered books"""
    print("\n" + "="*60)
    print("Suggested Mappings:")
    print("="*60)
    
    # Group assigned books
    ot_books = [b for b in assigned_books if 101 <= b <= 166]
    nt_books = [b for b in assigned_books if 240 <= b <= 266]
    
    if ot_books:
        print(f"\nOT Books (101-166): {ot_books[:10]}...")
        print(f"  Suggested rule: 101-166 → 1-66 (offset -100)")
    
    if nt_books:
        print(f"\nNT Books (240-266): {nt_books[:10]}...")
        print(f"  Suggested rule: 240-266 → 40-66 (offset -200)")
    
    # Check for outliers
    outliers = [b for b in assigned_books if not (101 <= b <= 166) and not (240 <= b <= 266)]
    if outliers:
        print(f"\n⚠️ Outliers found (not in expected ranges): {outliers}")
        print("  These may need specific mappings")


def main():
    print("="*60)
    print("Book Mapping Configuration Utility")
    print("="*60)
    
    # Discover books
    assigned = discover_assigned_books()
    translated = discover_translated_books()
    
    if assigned and translated:
        suggest_mappings(assigned, translated)
        
        # Create config with discovered mappings
        config = BookMappingConfig()
        
        # Save to file
        config_file = Path(__file__).parent.parent / "config" / "book_mappings.json"
        config.save_to_file(str(config_file))
        
        print(f"\n✅ Configuration saved to: {config_file}")
        print("\nYou can edit this file to add custom mappings.")
    else:
        print("\n❌ Could not discover books. Check database connection.")


if __name__ == '__main__':
    main()