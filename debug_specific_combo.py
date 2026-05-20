from core.database_manager import DatabaseManager
from config.database_config import DatabaseConfigManager

x = DatabaseManager(DatabaseConfigManager())
x.current_db = 'AG_Dev'
combo = 'Keoru- Ahia (Keoru)'
q = f"SELECT p.id, p.name, p.\"projectType\", COALESCE(d.name,'') as dialect_name, l.name as language_name FROM projects p JOIN languages l ON p.\"languageId\"=l.id LEFT JOIN dialects d ON p.\"dialectId\"=d.id WHERE l.name = 'Keoru- Ahia (Keoru)' OR d.name = 'Keoru- Ahia (Keoru)'"
try:
    df = x.execute_query(q)
    print(df)
except Exception as e:
    print('ERROR', e)
