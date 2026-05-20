from config.dialect_config import get_dialect_manager
from core.database_manager import DatabaseManager
from config.database_config import DatabaseConfigManager

x = DatabaseManager(DatabaseConfigManager())
x.current_db = 'AG_Dev'
manager = get_dialect_manager(x)
combos = manager.get_language_dialect_combinations()

for _, row in combos.iterrows():
    lang = row['language']
    dialect = row['dialect_name']

    if dialect:
        q = f"SELECT count(*) as cnt FROM projects p JOIN languages l ON p.\"languageId\"=l.id LEFT JOIN dialects d ON p.\"dialectId\"=d.id WHERE l.name='{lang.replace("'","''")}' AND d.name='{dialect.replace("'","''")}'"
    else:
        q = f"SELECT count(*) as cnt FROM projects p JOIN languages l ON p.\"languageId\"=l.id WHERE l.name='{lang.replace("'","''")}' AND (p.\"dialectId\" IS NULL OR p.\"dialectId\"='')"

    cnt = x.execute_query(q)['cnt'].iloc[0]
    if cnt > 1:
        print(lang, dialect, cnt)
