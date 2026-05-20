from core.database_manager import DatabaseManager
from config.database_config import DatabaseConfigManager

x = DatabaseManager(DatabaseConfigManager())
x.current_db = 'AG_Dev'
combo_language = 'Keoru- Ahia (Keoru)'
combo_dialect = 'Keoru- Ahia (Keoru)'

q = f"SELECT p.id, p.name as project_name, p.\"projectType\" as project_type, l.name as language_name, COALESCE(d.name, '') as dialect_name, COALESCE(d.\"rolvCode\", '') as rolv_code, p.\"dialectId\" as dialect_id, p.\"languageId\" as language_id FROM projects p JOIN languages l ON p.\"languageId\" = l.id LEFT JOIN dialects d ON p.\"dialectId\" = d.id WHERE l.name = '{combo_language.replace("'","''")}' AND d.name = '{combo_dialect.replace("'","''")}' ORDER BY project_name"

print('QUERY:')
print(q)
print('\nRESULTS:')
try:
    df = x.execute_query(q)
    if df.empty:
        print('No projects found')
    else:
        print(df.to_string(index=False))
except Exception as e:
    print('ERROR', e)
