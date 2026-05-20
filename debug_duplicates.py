from config.dialect_config import get_dialect_manager
from core.database_manager import DatabaseManager
from config.database_config import DatabaseConfigManager
import pandas as pd

dbm = DatabaseManager(DatabaseConfigManager())
dbm.current_db = 'AG_Dev'
dialect_manager = get_dialect_manager(dbm)
df = dialect_manager.get_language_dialect_combinations()
print('combos', len(df))
dup = df[df.duplicated(['country','language','dialect_name','rolv_code'], keep=False)]
print('duplicate combo rows', len(dup))
if not dup.empty:
    print(dup.head(20).to_string(index=False))
proj = dbm.execute_query("SELECT p.id, p.name, l.name as language, COALESCE(d.name, '') as dialect_name, p.\"projectType\" FROM projects p LEFT JOIN languages l ON p.\"languageId\"=l.id LEFT JOIN dialects d ON p.\"dialectId\"=d.id")
dup2 = proj[proj.duplicated(['id','language','dialect_name'], keep=False)]
print('dup projects rows', len(dup2))
if not dup2.empty:
    print(dup2.head(20).to_string(index=False))
