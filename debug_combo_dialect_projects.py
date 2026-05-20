from core.database_manager import DatabaseManager
from config.database_config import DatabaseConfigManager

x = DatabaseManager(DatabaseConfigManager())
x.current_db = 'AG_Dev'
combo_dialect = 'Keoru- Ahia (Keoru)'

q = f"SELECT DISTINCT c.name as country, l.name as language_name, COALESCE(d.name,'') as dialect_name, COALESCE(d.\"rolvCode\",'') as rolv_code, l.id as language_id, d.id as dialect_id FROM projects p JOIN languages l ON p.\"languageId\"=l.id LEFT JOIN dialects d ON p.\"dialectId\"=d.id LEFT JOIN countries c ON p.\"countryId\"=c.id WHERE COALESCE(d.name,'') = '{combo_dialect.replace("'","''")}' ORDER BY country, language_name, dialect_name"
print(q)
print() 
try:
    df = x.execute_query(q)
    print(df.to_string(index=False))
except Exception as e:
    print('ERROR', e)

q2 = f"SELECT p.id, p.name as project_name, p.\"projectType\" as project_type, l.name as language_name, COALESCE(d.name,'') as dialect_name, c.name as country FROM projects p JOIN languages l ON p.\"languageId\"=l.id LEFT JOIN dialects d ON p.\"dialectId\"=d.id LEFT JOIN countries c ON p.\"countryId\"=c.id WHERE COALESCE(d.name,'') = '{combo_dialect.replace("'","''")}' ORDER BY project_name"
print('\nPROJECTS QUERY:')
print(q2)
print()
try:
    df2 = x.execute_query(q2)
    print(df2.to_string(index=False))
except Exception as e:
    print('ERROR', e)
