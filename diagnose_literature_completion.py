#!/usr/bin/env python3
"""
Diagnose Literature Completion Data Linking Issues
Finds why completed work is not showing up against MTTs
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
print("LITERATURE COMPLETION DATA DIAGNOSTIC")
print("="*80)

# 1. Check the MTT assignments for Ginuman_Lit.
print("\n1. MTT ASSIGNMENTS FOR GINUMAN_LIT.:")
query = """
SELECT 
    u.id as user_id,
    u.username,
    u.name as user_name,
    utp."literatureGenres" as assigned_genres
FROM users_to_projects utp
JOIN users u ON utp."userId" = u.id
JOIN projects p ON utp."projectId" = p.id
WHERE p.name = 'Ginuman_Lit.'
  AND utp.role = 'MTT'
"""
df = db_manager.execute_query(query)
print(df.to_string())

print("\n2. COMPLETED GENRE RECORDS FOR GINUMAN_LIT.:")
query = """
SELECT 
    lg."genreId" as genre_type,
    lpg.version,
    lpg."userId" as completed_by_user_id,
    lpg.content,
    lpg."updatedAt"
FROM literature_project_genres_history lpg
JOIN literature_project_genres lg ON lpg."literatureProjectGenreId" = lg.id
JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
JOIN projects p ON lp."projectId" = p.id
WHERE p.name = 'Ginuman_Lit.'
  AND lpg.version > 1
ORDER BY lg."genreId"
"""
df = db_manager.execute_query(query)
print(df.to_string())

print("\n3. CHECK IF COMPLETED_BY_USER_ID MATCHES MTT USER IDs:")
print("   Completed by user IDs found:")
completed_users = df['completed_by_user_id'].unique() if not df.empty else []
print(f"   {completed_users}")

print("\n   MTT User IDs from assignments:")
mtt_users = df_assign['user_id'].tolist() if 'df_assign' in dir() else []
print(f"   {mtt_users}")

print("\n4. GET DETAILS OF THE COMPLETED_BY_USER:")
if completed_users:
    for user_id in completed_users:
        query = f"""
        SELECT id, username, name, email
        FROM users
        WHERE id = '{user_id}'
        """
        df_user = db_manager.execute_query(query)
        print(f"\n   User ID: {user_id}")
        if not df_user.empty:
            print(f"   Username: {df_user['username'].iloc[0]}")
            print(f"   Name: {df_user['name'].iloc[0]}")
            print(f"   Email: {df_user['email'].iloc[0]}")
        else:
            print(f"   ❌ User not found in users table!")

print("\n5. CHECK IF THERE'S A MISMATCH IN GENRE ID FORMAT:")
print("   Assigned genres format vs Completed genres format")

# Get assigned genres from first query
if not df.empty:
    assigned = df['assigned_genres'].iloc[0] if 'df' in dir() and not df.empty else ""
    print(f"   Assigned: {assigned}")
    
    # Get completed genres
    completed_genres = df['genre_type'].tolist() if 'df' in dir() and not df.empty else []
    print(f"   Completed: {completed_genres}")

print("\n6. CHECK LITERATURE_PROJECT_GENRES TABLE (not history):")
query = """
SELECT 
    lg."genreId",
    lg.version,
    lg."updatedAt"
FROM literature_project_genres lg
JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
JOIN projects p ON lp."projectId" = p.id
WHERE p.name = 'Ginuman_Lit.'
ORDER BY lg."genreId"
"""
df_main = db_manager.execute_query(query)
print(df_main.to_string())

print("\n7. VERIFY THE CONTENT EXISTS FOR EACH GENRE:")
for genre in completed_genres:
    query = f"""
    SELECT 
        lg."genreId",
        lpg.content::text as content_preview
    FROM literature_project_genres_history lpg
    JOIN literature_project_genres lg ON lpg."literatureProjectGenreId" = lg.id
    JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
    JOIN projects p ON lp."projectId" = p.id
    WHERE p.name = 'Ginuman_Lit.'
      AND lg."genreId" = '{genre}'
      AND lpg.version > 1
    LIMIT 1
    """
    df_content = db_manager.execute_query(query)
    if not df_content.empty:
        content = df_content['content_preview'].iloc[0]
        # Check if content has actual text
        if content and 'content' in content:
            # Try to parse and count
            try:
                data = json.loads(content)
                if 'content' in data:
                    blocks = data['content']
                    filled = sum(1 for b in blocks if isinstance(b, dict) and b.get('content', '').strip())
                    print(f"   {genre}: {filled}/{len(blocks)} blocks filled")
            except:
                print(f"   {genre}: Content exists but couldn't parse")
    else:
        print(f"   {genre}: ❌ No content found")

print("\n" + "="*80)
print("RECOMMENDED FIX:")
print("="*80)
print("""
The issue appears to be that:
1. The completed_by_user_id in history table may not match the MTT user ID
2. Or the genre ID format might be different (e.g., 'poetry' vs 'lit:poetry')

To fix:
- Update the join logic to match by email or username instead of user_id
- Or normalize genre IDs to remove 'lit:' prefix for comparison
""")
