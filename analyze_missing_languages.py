#!/usr/bin/env python3
"""Analyze which languages are missing from the report"""

import sys
sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager

db_config = DatabaseConfigManager()
db_manager = DatabaseManager(db_config)
db_manager.current_db = 'AG_Dev'

# Get all languages that have projects but no dialect assigned
query = """
SELECT 
    c.name as country,
    l.name as language,
    COUNT(DISTINCT p.id) as project_count,
    STRING_AGG(DISTINCT p."projectType", ', ') as project_types
FROM projects p
LEFT JOIN languages l ON p."languageId" = l.id
LEFT JOIN countries c ON p."countryId" = c.id
WHERE p."projectType" IN ('TEXT_TRANSLATION', 'OBS', 'LITERATURE', 'LITERATURE_PROJECT',
                          'GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
  AND c.name IS NOT NULL
  AND p."dialectId" IS NULL
GROUP BY c.name, l.name
ORDER BY c.name, l.name
"""

print("📊 Languages with projects but NO dialect assigned (currently MISSING from report):")
print("=" * 70)
df = db_manager.execute_query(query)
if not df.empty:
    for _, row in df.iterrows():
        print(f"  {row['country']} - {row['language']}: {row['project_count']} project(s) [{row['project_types']}]")
    print(f"\n  Total: {len(df)} languages missing")
else:
    print("  None found - all languages have dialects?")

# Also check languages that have neither projects nor dialects
print("\n" + "=" * 70)
print("📊 Languages in database (for reference):")
lang_query = "SELECT name FROM languages ORDER BY name LIMIT 20"
lang_df = db_manager.execute_query(lang_query)
if not lang_df.empty:
    for _, row in lang_df.iterrows():
        print(f"  {row['name']}")
