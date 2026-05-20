from core.database_manager import DatabaseManager
from config.database_config import DatabaseConfigManager

x = DatabaseManager(DatabaseConfigManager())
x.current_db = 'AG_Dev'
search = 'Keoru'
q = f"SELECT DISTINCT c.name as country, l.name as language_name, COALESCE(d.name,'') as dialect_name, COALESCE(d.\"rolvCode\",'') as rolv_code, l.id as language_id, d.id as dialect_id FROM projects p JOIN languages l ON p.\"languageId\"=l.id LEFT JOIN dialects d ON p.\"dialectId\"=d.id LEFT JOIN countries c ON p.\"countryId\"=c.id WHERE l.name ILIKE '%{search}%' OR COALESCE(d.name,'') ILIKE '%{search}%' ORDER BY country, language_name, dialect_name"
print(q)
print()
try:
    df = x.execute_query(q)
    print(df.to_string(index=False))
except Exception as e:
    print('ERROR', e)

search2 = 'Tainae'
q2 = f"SELECT DISTINCT c.name as country, l.name as language_name, COALESCE(d.name,'') as dialect_name, COALESCE(d.\"rolvCode\",'') as rolv_code, l.id as language_id, d.id as dialect_id FROM projects p JOIN languages l ON p.\"languageId\"=l.id LEFT JOIN dialects d ON p.\"dialectId\"=d.id LEFT JOIN countries c ON p.\"countryId\"=c.id WHERE l.name ILIKE '%{search2}%' OR COALESCE(d.name,'') ILIKE '%{search2}%' ORDER BY country, language_name, dialect_name"
print('\n', q2)
print()
try:
    df2 = x.execute_query(q2)
    print(df2.to_string(index=False))
except Exception as e:
    print('ERROR', e)
