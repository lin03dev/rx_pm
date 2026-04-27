#!/usr/bin/env python3
"""
Analyze Grammar MTT-level completion - Check if each MTT has their own progress
"""

import sys
import json
sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager

db_config = DatabaseConfigManager()
db_manager = DatabaseManager(db_config)
db_manager.current_db = 'AG_Dev'

print("="*80)
print("GRAMMAR MTT-LEVEL COMPLETION ANALYSIS")
print("="*80)

# Check Abbey_G.Phrases project
print("\n1. CHECKING ABBEY_G.PHRASES PROJECT:")
query = """
SELECT 
    p.id as project_id,
    p.name as project_name,
    gp.id as grammar_project_id
FROM projects p
JOIN grammar_phrases_projects gp ON p.id = gp."projectId"
WHERE p.name = 'Abbey_G.Phrases'
"""
df = db_manager.execute_query(query)
print(df.to_string())

if not df.empty:
    project_id = df['project_id'].iloc[0]
    grammar_project_id = df['grammar_project_id'].iloc[0]
    
    print(f"\n   Project ID: {project_id}")
    print(f"   Grammar Project ID: {grammar_project_id}")
    
    # Check MTTs assigned to this project
    print("\n2. MTTS ASSIGNED TO ABBEY_G.PHRASES:")
    query2 = """
    SELECT 
        u.id as user_id,
        u.username,
        u.name as full_name
    FROM users_to_projects utp
    JOIN users u ON utp."userId" = u.id
    WHERE utp."projectId" = '%s'
      AND utp.role = 'MTT'
    """ % project_id
    df2 = db_manager.execute_query(query2)
    print(df2.to_string())
    
    # Check content records and who created them
    print("\n3. CONTENT RECORDS WITH USER IDs:")
    query3 = """
    SELECT 
        gpc.version,
        gpc.content,
        gpc."userId" as created_by
    FROM grammar_phrases_project_contents gpc
    WHERE gpc."grammarPhrasesProjectId" = '%s'
    ORDER BY gpc.version DESC
    """ % grammar_project_id
    df3 = db_manager.execute_query(query3)
    
    for _, row in df3.iterrows():
        print(f"\n   Version: {row['version']}")
        print(f"   Created By: {row['created_by']}")
        content = row['content']
        if content:
            try:
                if isinstance(content, str):
                    data = json.loads(content)
                else:
                    data = content
                
                if 'content' in data:
                    items = data['content']
                    total = len(items)
                    completed = sum(1 for i in items if isinstance(i, dict) and i.get('phrase', '').strip())
                    print(f"   Total Items: {total}")
                    print(f"   Completed Items: {completed}")
                    print(f"   Completion %: {completed/total*100:.1f}%")
            except:
                print(f"   Could not parse content")
    
    # Check if there are multiple versions from different users
    print("\n4. CHECKING IF DIFFERENT MTTS HAVE DIFFERENT VERSIONS:")
    query4 = """
    SELECT 
        gpc."userId" as user_id,
        COUNT(*) as version_count,
        MAX(gpc.version) as max_version
    FROM grammar_phrases_project_contents gpc
    WHERE gpc."grammarPhrasesProjectId" = '%s'
    GROUP BY gpc."userId"
    """ % grammar_project_id
    df4 = db_manager.execute_query(query4)
    print(df4.to_string())

