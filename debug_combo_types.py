from core.database_manager import DatabaseManager
from config.database_config import DatabaseConfigManager

x = DatabaseManager(DatabaseConfigManager())
x.current_db = 'AG_Dev'
q = "SELECT p.\"projectType\", count(*) as cnt FROM projects p JOIN languages l ON p.\"languageId\"=l.id LEFT JOIN dialects d ON p.\"dialectId\"=d.id WHERE l.name = 'Keoru- Ahia (Keoru)' OR d.name = 'Keoru- Ahia (Keoru)' GROUP BY p.\"projectType\""
print(x.execute_query(q))
