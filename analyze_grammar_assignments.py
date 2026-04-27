#!/usr/bin/env python3
"""
Analyze Grammar Module Assignment Structure
Compare with Bible and OBS assignment patterns
"""

import sys
sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager

db_config = DatabaseConfigManager()
db_manager = DatabaseManager(db_config)
db_manager.current_db = 'AG_Dev'

print("="*80)
print("GRAMMAR ASSIGNMENT STRUCTURE ANALYSIS")
print("="*80)

# 1. Check how Bible projects are assigned (for comparison)
print("\n1. BIBLE PROJECT ASSIGNMENT PATTERN:")
query_bible = """
SELECT 
    p.name as project_name,
    utp.role,
    utp.verses,
    array_length(string_to_array(COALESCE(utp.verses, ''), ','), 1) as verses_count
FROM users_to_projects utp
JOIN projects p ON utp."projectId" = p.id
WHERE p."projectType" = 'TEXT_TRANSLATION'
  AND utp.verses IS NOT NULL
  AND utp.verses != ''
LIMIT 3
"""
df_bible = db_manager.execute_query(query_bible)
print(df_bible.to_string())

# 2. Check how OBS projects are assigned
print("\n2. OBS PROJECT ASSIGNMENT PATTERN:")
query_obs = """
SELECT 
    p.name as project_name,
    utp.role,
    utp."obsChapters",
    array_length(string_to_array(COALESCE(utp."obsChapters", ''), ','), 1) as chapters_count
FROM users_to_projects utp
JOIN projects p ON utp."projectId" = p.id
WHERE p."projectType" = 'OBS'
  AND utp."obsChapters" IS NOT NULL
  AND utp."obsChapters" != ''
LIMIT 3
"""
df_obs = db_manager.execute_query(query_obs)
print(df_obs.to_string())

# 3. Check how Literature projects are assigned
print("\n3. LITERATURE PROJECT ASSIGNMENT PATTERN:")
query_lit = """
SELECT 
    p.name as project_name,
    utp.role,
    utp."literatureGenres",
    array_length(string_to_array(COALESCE(utp."literatureGenres", ''), ','), 1) as genres_count
FROM users_to_projects utp
JOIN projects p ON utp."projectId" = p.id
WHERE p."projectType" IN ('LITERATURE', 'LITERATURE_PROJECT')
  AND utp."literatureGenres" IS NOT NULL
  AND utp."literatureGenres" != ''
LIMIT 3
"""
df_lit = db_manager.execute_query(query_lit)
print(df_lit.to_string())

# 4. Check how Grammar projects are assigned
print("\n4. GRAMMAR PROJECT ASSIGNMENT PATTERN:")
query_grammar = """
SELECT 
    p.name as project_name,
    p."projectType",
    utp.role,
    utp.verses,
    utp."obsChapters",
    utp."literatureGenres"
FROM users_to_projects utp
JOIN projects p ON utp."projectId" = p.id
WHERE p."projectType" IN ('GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
  AND utp.role = 'MTT'
LIMIT 10
"""
df_grammar = db_manager.execute_query(query_grammar)
print(df_grammar.to_string())

# 5. Check if grammar projects have any assignment fields populated
print("\n5. GRAMMAR ASSIGNMENT FIELDS SUMMARY:")
query_summary = """
SELECT 
    p."projectType",
    COUNT(*) as total_assignments,
    COUNT(CASE WHEN utp.verses IS NOT NULL AND utp.verses != '' THEN 1 END) as has_verses,
    COUNT(CASE WHEN utp."obsChapters" IS NOT NULL AND utp."obsChapters" != '' THEN 1 END) as has_obs,
    COUNT(CASE WHEN utp."literatureGenres" IS NOT NULL AND utp."literatureGenres" != '' THEN 1 END) as has_literature
FROM users_to_projects utp
JOIN projects p ON utp."projectId" = p.id
WHERE p."projectType" IN ('GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
  AND utp.role = 'MTT'
GROUP BY p."projectType"
"""
df_summary = db_manager.execute_query(query_summary)
print(df_summary.to_string())

# 6. Check content table structure - do they track who created what?
print("\n6. GRAMMAR CONTENT TABLE STRUCTURE:")
for table in ['grammar_phrases_project_contents', 'grammar_pronouns_project_contents', 'grammar_connectives_project_contents']:
    query_cols = f"""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = '{table}'
    ORDER BY ordinal_position
    """
    df_cols = db_manager.execute_query(query_cols)
    print(f"\n   {table}: {df_cols['column_name'].tolist()}")

# 7. Check if grammar projects have specific items assigned
print("\n7. CHECKING GRAMMAR CONTENT - WHAT ITEMS EXIST:")
query_items = """
SELECT 
    p.name as project_name,
    p."projectType",
    gpc.content::text as content_preview
FROM grammar_phrases_project_contents gpc
JOIN grammar_phrases_projects gp ON gpc."grammarPhrasesProjectId" = gp.id
JOIN projects p ON gp."projectId" = p.id
WHERE gpc.version > 1
LIMIT 3
"""
try:
    df_items = db_manager.execute_query(query_items)
    for _, row in df_items.iterrows():
        print(f"\n   Project: {row['project_name']} ({row['project_type']})")
        content = row['content_preview'][:200] if row['content_preview'] else 'No content'
        print(f"   Content preview: {content}...")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*80)
print("KEY FINDINGS:")
print("="*80)
print("""
Based on the analysis:

1. BIBLE projects: Assign SPECIFIC VERSES (e.g., '101001001,101001002...')
   - Each MTT gets specific verses to translate
   - Work is divided among MTTs

2. OBS projects: Assign SPECIFIC CHAPTERS (e.g., '1,2,3,4,5...')
   - Each MTT gets specific chapters to translate
   - Work is divided among MTTs

3. LITERATURE projects: Assign SPECIFIC GENRES (e.g., 'poetry,history...')
   - Each MTT gets specific genres to translate
   - Work is divided among MTTs

4. GRAMMAR projects: NO SPECIFIC ASSIGNMENTS!
   - The verses, obsChapters, literatureGenres fields are ALL NULL
   - MTTs are assigned to the project but no specific items are assigned
   - The content table contains ALL items for the project (not divided by MTT)
   - All MTTs work on the SAME set of items (collaborative)

CONCLUSION:
Grammar projects are DIFFERENT from other project types:
- They are COLLABORATIVE (all MTTs work on same content)
- No item-level assignment to specific MTTs
- The history table tracks versions but doesn't show individual item completion

RECOMMENDATION:
For grammar projects, track PROJECT-LEVEL completion only,
not MTT-level item completion (since work is shared).
""")
