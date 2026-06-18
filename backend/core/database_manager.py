"""
Database Manager - Simplified with direct psycopg2 connection
"""

import pandas as pd
import psycopg2
from typing import Dict, Any, Optional, List
import logging
from config.database_config import DatabaseConfigManager, DatabaseType
from config.book_mapping_config import get_book_mapping_config, map_book, map_verse_id

# Suppress the pandas warning about psycopg2 connections
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections using psycopg2 directly"""
    
    def __init__(self, config_manager: DatabaseConfigManager):
        self.config_manager = config_manager
        self.connections: Dict[str, Any] = {}
        self.book_mapping_config = get_book_mapping_config()
        self._current_db: Optional[str] = None
    
    @property
    def current_db(self) -> Optional[str]:
        return self._current_db
    
    @current_db.setter
    def current_db(self, value: Optional[str]):
        self._current_db = value
    
    def _get_connection(self, db_name: str):
        """Get or create database connection"""
        if db_name not in self.connections:
            config = self.config_manager.get_config(db_name)
            if not config:
                raise ValueError(f"Database configuration not found: {db_name}")
            
            if config.db_type == DatabaseType.POSTGRESQL:
                connect_kwargs = {
                    'host': config.host,
                    'port': config.port,
                    'database': config.database,
                    'user': config.user,
                    'password': config.password,
                }
                if config.ssl_mode:
                    connect_kwargs['sslmode'] = config.ssl_mode
                conn = psycopg2.connect(**connect_kwargs)
                conn.autocommit = True  # Prevent transaction issues
                self.connections[db_name] = conn
        
        return self.connections[db_name]
    
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
    
    def _read_sql(self, query: str, params: Optional[Any] = None, db_name: Optional[str] = None) -> pd.DataFrame:
        """Run read_sql_query with pandas SQLAlchemy warnings suppressed."""
        use_db = db_name or self.current_db
        if not use_db:
            raise ValueError("No database specified.")

        conn = self._get_connection(use_db)
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*SQLAlchemy connectable.*",
                category=UserWarning,
            )
            if params is not None:
                return pd.read_sql_query(query, conn, params=params)
            return pd.read_sql_query(query, conn)

    def execute_query(self, query: str, params: Optional[tuple] = None, 
                      db_name: Optional[str] = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        use_db = db_name or self.current_db
        if not use_db:
            raise ValueError("No database specified.")
        
        try:
            return self._read_sql(query, params, db_name=use_db)
        except Exception as e:
            conn = self.connections.get(use_db)
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Query execution error: {e}")
            return pd.DataFrame()
    
    def execute_update(self, query: str, params: Optional[tuple] = None,
                       db_name: Optional[str] = None) -> int:
        use_db = db_name or self.current_db
        if not use_db:
            raise ValueError("No database specified")
        
        conn = self._get_connection(use_db)
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
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

        query = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
            AND lower(table_name) = lower(%s)
        )
        """
        try:
            conn = self._get_connection(use_db)
            with conn.cursor() as cursor:
                cursor.execute(query, (table_name,))
                row = cursor.fetchone()
                return bool(row[0]) if row else False
        except Exception as exc:
            logger.warning("table_exists failed for %s on %s: %s", table_name, use_db, exc)
            return False
    
    def reset_connection(self, db_name: Optional[str] = None):
        """Reset connection to clear any transaction errors"""
        use_db = db_name or self.current_db
        if use_db and use_db in self.connections:
            try:
                self.connections[use_db].close()
            except:
                pass
            del self.connections[use_db]
    
    def close(self):
        """Close all database connections"""
        for conn in self.connections.values():
            try:
                conn.close()
            except:
                pass
        self.connections.clear()
