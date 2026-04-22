"""
Base Report Class - All reports inherit from this
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
import pandas as pd
from core.database_manager import DatabaseManager
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
        self.book_mapping = get_book_mapping_config()
    
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
    
    @abstractmethod
    def get_sheet_names(self) -> Dict[str, str]:
        """Get sheet names for multi-sheet reports"""
        pass
    
    def apply_filters(self, filters: Dict[str, Any]):
        """Apply filters to the report"""
        self.filters.update(filters)
        logger.info(f"Applied filters: {filters}")
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """Execute query with the configured database"""
        return self.db_manager.execute_query(query, params, db_name=self.db_name)
    
    def validate_data(self, df: pd.DataFrame, min_rows: int = 0) -> bool:
        """Validate generated data"""
        if df.empty:
            logger.warning(f"DataFrame is empty")
            return False
        if len(df) < min_rows:
            logger.warning(f"DataFrame has only {len(df)} rows, expected at least {min_rows}")
            return False
        return True