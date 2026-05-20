from core.database_manager import DatabaseManager
from config.database_config import DatabaseConfigManager

x = DatabaseManager(DatabaseConfigManager())
x.current_db = 'AG_Dev'
lang = 'Keoru- Ahia (Keoru)'
q = f"SELECT p.id, p.name, p.\"projectType\" as project_type, p.\"dialectId\" FROM projects p JOIN languages l ON p.\"languageId\"=l.id WHERE l.name = '{lang.replace("'","''")}' AND (p.\"dialectId\" IS NULL OR p.\"dialectId\" = '') ORDER BY p.name"
print(q)
print()
df = x.execute_query(q)
print(df.to_string(index=False))
print('\nCOUNT', len(df))
