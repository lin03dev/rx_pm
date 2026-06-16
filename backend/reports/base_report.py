"""
Base Report Class - All reports inherit from this
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
import pandas as pd
from core.database_manager import DatabaseManager
from core.schema_guard import SchemaGuard, SchemaViolationError
from config.book_mapping_config import get_book_mapping_config, map_book, map_verse_id, get_book_name
import logging

logger = logging.getLogger(__name__)

class BaseReport(ABC):
    """Abstract base class for all reports"""
    
    def __init__(self, db_manager: DatabaseManager, **kwargs):
        self.db_manager = db_manager
        self.filters = {}
        self.params = kwargs
        self.data = {}
        self.db_name = kwargs.get('db_name')
        self.report_id = kwargs.get('report_id')
        self.available_filters = []
        self.book_mapping = get_book_mapping_config()
        self.schema = SchemaGuard(db_manager, self.db_name, self.report_id)
        if self.db_name and self.report_id:
            self.schema.validate_primary_connection()
        self._apply_schema_catalog()
    
    def map_assigned_book(self, book_number: int) -> int:
        """Map assigned book number to standard Bible book number"""
        return map_book(book_number)
    
    def map_assigned_verse(self, verse_id: str) -> str:
        """Map assigned verse ID to standard format"""
        return map_verse_id(verse_id)
    
    def get_assigned_verses_set(self, verses_string: str) -> Set[str]:
        """Parse assigned verses and return set of mapped verse IDs"""
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
    
    def get_book_name(self, book_number: int) -> str:
        """Get the English name of a Bible book"""
        return get_book_name(book_number)
    
    @abstractmethod
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate report data"""
        pass

    def _apply_schema_catalog(self) -> None:
        from config.report_schema import get_available_filters

        if self.report_id:
            self.available_filters = get_available_filters(self.report_id)

    def get_sheet_names(self) -> Dict[str, str]:
        from config.report_schema import get_sheet_names as schema_sheet_names

        if self.report_id:
            return schema_sheet_names(self.report_id)
        return {}
    
    def apply_filters(self, filters: Dict[str, Any]):
        """Apply filters to the report"""
        self.filters.update(filters)
        logger.info(f"Applied filters: {filters}")

    def schema_order_columns(self, sheet_key: str, df: pd.DataFrame) -> pd.DataFrame:
        """Order DataFrame columns using schema_registry report_definitions."""
        if not self.report_id or df.empty:
            return df
        from config.report_schema import order_dataframe_columns

        return order_dataframe_columns(self.report_id, sheet_key, df)
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """Execute query; constrained to registered schema tables when configured."""
        if self.db_name and self.report_id and self.schema.system:
            tables = self.schema.extract_schema_tables(query)
            if not tables:
                raise SchemaViolationError(
                    "Query must reference registered schema tables via FROM or JOIN clauses"
                )
            return self.schema.query(query, tables, params=params)
        return self.db_manager.execute_query(query, params, db_name=self.db_name)

    def companion_schema_query(
        self,
        target_system: str,
        query: str,
        tables: List[str],
        params: Optional[Dict] = None,
    ) -> pd.DataFrame:
        """Run a query on an allowed companion database (cross-db reports only)."""
        return self.schema.companion_query(target_system, query, tables, params=params)

    def schema_query(self, query: str, tables: List[str], params: Optional[Dict] = None) -> pd.DataFrame:
        """Execute a query constrained to registered schema tables."""
        return self.schema.query(query, tables, params=params)

    def schema_message(self, message: str) -> pd.DataFrame:
        return self.schema.message_frame(message)
    
    def validate_data(self, df: pd.DataFrame, min_rows: int = 0) -> bool:
        """Validate generated data"""
        if df.empty:
            logger.warning(f"DataFrame is empty")
            return False
        if len(df) < min_rows:
            logger.warning(f"DataFrame has only {len(df)} rows, expected at least {min_rows}")
            return False
        return True
