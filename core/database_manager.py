"""
Database Manager - Handles all database operations with SQLAlchemy
"""

import pandas as pd
from sqlalchemy import create_engine, text
from typing import Dict, Any, Optional, List, Tuple
import logging
from config.database_config import DatabaseConfigManager, DatabaseType
from config.book_mapping_config import get_book_mapping_config, map_book, map_verse_id

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations with SQLAlchemy"""
    
    def __init__(self, config_manager: DatabaseConfigManager):
        self.config_manager = config_manager
        self.engines: Dict[str, Any] = {}
        self.book_mapping = get_book_mapping_config()
        self._current_db: Optional[str] = None
    
    @property
    def current_db(self) -> Optional[str]:
        return self._current_db
    
    @current_db.setter
    def current_db(self, value: Optional[str]):
        self._current_db = value
    
    def _get_engine(self, db_name: str):
        """Get or create SQLAlchemy engine for a database"""
        if db_name not in self.engines:
            config = self.config_manager.get_config(db_name)
            if not config:
                raise ValueError(f"Database configuration not found: {db_name}")
            
            if config.db_type == DatabaseType.POSTGRESQL:
                conn_string = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}"
                if config.ssl_mode and config.ssl_mode != 'disable':
                    conn_string += f"?sslmode={config.ssl_mode}"
                
                self.engines[db_name] = create_engine(conn_string)
        
        return self.engines[db_name]
    
    def map_assigned_verse(self, verse_id: str) -> str:
        return map_verse_id(verse_id)
    
    def map_assigned_book(self, book_number: int) -> int:
        return map_book(book_number)
    
    def get_assigned_verses_set(self, verses_string: str) -> set:
        result = set()
        if not verses_string:
            return result
        for verse_id in verses_string.split(','):
            verse_id = verse_id.strip()
            if verse_id and len(verse_id) >= 6:
                try:
                    mapped_id = self.map_assigned_verse(verse_id)
                    result.add(mapped_id)
                except:
                    result.add(verse_id)
        return result
    
    def execute_query(self, query: str, params: Optional[tuple] = None, 
                      db_name: Optional[str] = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        use_db = db_name or self.current_db
        if not use_db:
            raise ValueError("No database specified. Set current_db or pass db_name parameter.")
        
        engine = self._get_engine(use_db)
        try:
            if params:
                # Convert dict to tuple if needed
                if isinstance(params, dict):
                    params = tuple(params.values())
                df = pd.read_sql_query(text(query), engine, params=params)
            else:
                df = pd.read_sql_query(query, engine)
            return df
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_update(self, query: str, params: Optional[tuple] = None,
                       db_name: Optional[str] = None) -> int:
        use_db = db_name or self.current_db
        if not use_db:
            raise ValueError("No database specified")
        
        engine = self._get_engine(use_db)
        with engine.connect() as conn:
            if params:
                if isinstance(params, dict):
                    params = tuple(params.values())
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            conn.commit()
            return result.rowcount
    
    def get_all_tables(self, db_name: Optional[str] = None) -> List[str]:
        use_db = db_name or self.current_db
        if not use_db:
            raise ValueError("No database specified")
        
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        df = self.execute_query(query, db_name=use_db)
        return df['table_name'].tolist() if not df.empty else []
    
    def get_table_count(self, table_name: str, db_name: Optional[str] = None) -> int:
        use_db = db_name or self.current_db
        if not use_db:
            return 0
        
        try:
            query = f'SELECT COUNT(*) as count FROM "{table_name}"'
            df = self.execute_query(query, db_name=use_db)
            return df['count'].iloc[0] if not df.empty else 0
        except:
            try:
                query = f"SELECT COUNT(*) as count FROM {table_name}"
                df = self.execute_query(query, db_name=use_db)
                return df['count'].iloc[0] if not df.empty else 0
            except:
                return 0
    
    def table_exists(self, table_name: str, db_name: Optional[str] = None) -> bool:
        use_db = db_name or self.current_db
        if not use_db:
            return False
        
        query = f"""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}'
        )
        """
        df = self.execute_query(query, db_name=use_db)
        return df.iloc[0, 0] if not df.empty else False
