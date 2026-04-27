#!/usr/bin/env python3
"""
Deep analysis of grammar data to understand structure and MTT-level completion
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
print("GRAMMAR DATA STRUCTURE ANALYSIS")
print("="*80)

# 1. Check Abbey_G.Phrases project
print("\n1. ABBEY_G.PHRASES PROJECT:")
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
    
    # 2. Check MTTs assigned
    print("\n2. MTTS ASSIGNED TO THIS PROJECT:")
    query2 = f"""
    SELECT 
        u.id as user_id,
        u.username,
        u.name as full_name,
        u.email
    FROM users_to_projects utp
    JOIN users u ON utp."userId" = u.id
    WHERE utp."projectId" = '{project_id}'
      AND utp.role = 'MTT'
    """
    df2 = db_manager.execute_query(query2)
    print(df2.to_string())
    
    # 3. Check CONTENT table (without userId)
    print("\n3. CONTENT TABLE (current state):")
    query3 = f"""
    SELECT 
        gpc.version,
        gpc.content
    FROM grammar_phrases_project_contents gpc
    WHERE gpc."grammarPhrasesProjectId" = '{grammar_project_id}'
    ORDER BY gpc.version DESC
    LIMIT 1
    """
    df3 = db_manager.execute_query(query3)
    for idx, row in df3.iterrows():
        print(f"   Version: {row['version']}")
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
                    print(f"   Total items: {total}")
                    print(f"   Completed items: {completed}")
                    print(f"   Completion %: {completed/total*100:.1f}%")
            except Exception as e:
                print(f"   Error: {e}")
    
    # 4. Check HISTORY table (has userId)
    print("\n4. HISTORY TABLE (version history with userId):")
    query4 = f"""
    SELECT 
        gpc.version,
        gpc."userId" as created_by,
        gpc."createdAt"
    FROM grammar_phrases_project_content_history gpc
    WHERE gpc."grammarPhrasesProjectContentId" = '{grammar_project_id}'
    ORDER BY gpc.version DESC
    LIMIT 10
    """
    df4 = db_manager.execute_query(query4)
    print(df4.to_string())
    
    # 5. For each MTT, find their versions and what they contributed
    print("\n5. MTT CONTRIBUTION ANALYSIS:")
    mtts = df2.to_dict('records')
    
    for mtt in mtts:
        user_id = mtt['user_id']
        username = mtt['username']
        print(f"\n   MTT: {username} ({mtt['full_name']})")
        
        # Find versions created by this MTT
        query5 = f"""
        SELECT 
            gpc.version,
            gpc.content
        FROM grammar_phrases_project_content_history gpc
        WHERE gpc."grammarPhrasesProjectContentId" = '{grammar_project_id}'
          AND gpc."userId" = '{user_id}'
        ORDER BY gpc.version DESC
        LIMIT 1
        """
        df5 = db_manager.execute_query(query5)
        
        if not df5.empty:
            row = df5.iloc[0]
            content = row['content']
            version = row['version']
            print(f"      Latest version by this MTT: {version}")
            
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
                        print(f"      Items completed in this version: {completed}/{total} ({completed/total*100:.1f}%)")
                except:
                    pass
        else:
            print(f"      No content created by this MTT (may have only edited existing)")

# 6. Check how many MTTs have actually created content
print("\n" + "="*80)
print("6. OVERALL MTT CONTRIBUTION SUMMARY:")
query6 = """
SELECT 
    gpc."userId" as user_id,
    COUNT(*) as version_count,
    MAX(gpc.version) as max_version
FROM grammar_phrases_project_content_history gpc
GROUP BY gpc."userId"
ORDER BY version_count DESC
"""
df6 = db_manager.execute_query(query6)
print("\n   Grammar Phrases - MTT Contributions:")
for _, row in df6.iterrows():
    user_id = row['user_id']
    version_count = row['version_count']
    max_version = row['max_version']
    # Get username
    query_user = f"SELECT username, name FROM users WHERE id = '{user_id}'"
    df_user = db_manager.execute_query(query_user)
    username = df_user['username'].iloc[0] if not df_user.empty else user_id[:8]
    name = df_user['name'].iloc[0] if not df_user.empty and df_user['name'].iloc[0] else username
    print(f"      {name} ({username}): {version_count} versions, latest v{max_version}")

print("\n" + "="*80)
print("KEY FINDINGS:")
print("="*80)
print("""
Based on the analysis:

1. The CONTENT table stores the CURRENT state (final result)
   - No userId column - it's just the latest version
   
2. The HISTORY table stores VERSION HISTORY
   - Has userId column - tracks who created each version
   - Multiple versions can exist from different MTTs
   
3. For MTT-level completion reporting:
   - Option A: Show the LATEST version created by each MTT
   - Option B: Show the DIFFERENCE between what each MTT added
   - Option C: For grammar, it's better to show PROJECT-LEVEL completion
              because multiple MTTs collaborate on the same content
   
4. Recommendation: 
   - Keep project-level completion (which is accurate)
   - For MTT performance, show which MTTs contributed (version history)
   - Don't try to split items per MTT unless items are explicitly assigned
""")
