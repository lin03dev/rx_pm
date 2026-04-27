#!/usr/bin/env python3
"""
Verify user activity data accuracy
"""

import sys
sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager

db_config = DatabaseConfigManager()
db_manager = DatabaseManager(db_config)
db_manager.current_db = 'AG_Dev'

print("="*80)
print("VERIFYING USER ACTIVITY DATA")
print("="*80)

# 1. Check a user who should have activity (e.g., Hanok kurian - AG-482912)
print("\n1. CHECKING USER: AG-482912 (Hanok kurian)")
query = """
SELECT 
    u.id,
    u.username,
    u.name,
    u."createdAt",
    COUNT(w.id) as worklog_count,
    MIN(w."startDate") as first_activity,
    MAX(w."endDate") as last_activity
FROM users u
LEFT JOIN worklogs w ON u.id = w."userId"
WHERE u.username = 'AG-482912'
GROUP BY u.id, u.username, u.name, u."createdAt"
"""
df = db_manager.execute_query(query)
print(df.to_string())

# 2. Check worklogs for this user
print("\n2. WORKLOGS FOR AG-482912 (last 5):")
query2 = """
SELECT 
    w."startDate",
    w."endDate",
    w."noWork",
    p.name as project_name
FROM worklogs w
LEFT JOIN projects p ON w."projectId" = p.id
WHERE w."userId" = (SELECT id FROM users WHERE username = 'AG-482912')
ORDER BY w."endDate" DESC
LIMIT 5
"""
df2 = db_manager.execute_query(query2)
print(df2.to_string())

# 3. Check a sample of users who have worklogs
print("\n3. SAMPLE USERS WITH WORKLOGS:")
query3 = """
SELECT 
    u.username,
    u.name,
    COUNT(w.id) as worklog_count,
    MAX(w."endDate") as last_activity
FROM users u
JOIN worklogs w ON u.id = w."userId"
WHERE w."noWork" = false
GROUP BY u.id, u.username, u.name
ORDER BY worklog_count DESC
LIMIT 10
"""
df3 = db_manager.execute_query(query3)
print(df3.to_string())

# 4. Check total worklogs distribution
print("\n4. WORKLOG DISTRIBUTION:")
query4 = """
SELECT 
    CASE 
        WHEN wcount = 0 THEN 'No worklogs'
        WHEN wcount BETWEEN 1 AND 10 THEN '1-10 worklogs'
        WHEN wcount BETWEEN 11 AND 50 THEN '11-50 worklogs'
        WHEN wcount BETWEEN 51 AND 100 THEN '51-100 worklogs'
        ELSE '100+ worklogs'
    END as category,
    COUNT(*) as user_count
FROM (
    SELECT u.id, COUNT(w.id) as wcount
    FROM users u
    LEFT JOIN worklogs w ON u.id = w."userId" AND w."noWork" = false
    WHERE u.role::text != 'SUPER_ADMIN'
    GROUP BY u.id
) t
GROUP BY category
ORDER BY 
    CASE 
        WHEN category = 'No worklogs' THEN 1
        WHEN category = '1-10 worklogs' THEN 2
        WHEN category = '11-50 worklogs' THEN 3
        WHEN category = '51-100 worklogs' THEN 4
        ELSE 5
    END
"""
df4 = db_manager.execute_query(query4)
print(df4.to_string())

