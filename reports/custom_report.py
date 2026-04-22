"""
Custom Report - User-defined SQL reports
"""

import pandas as pd
from typing import Dict, Any
from reports.base_report import BaseReport

class CustomReport(BaseReport):
    """Custom Report - Execute user-provided SQL queries"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.query = kwargs.get('query', '')
        self.params = kwargs.get('params', {})
        self.available_filters = []
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Execute custom query and return results"""
        if not self.query:
            return {'error': pd.DataFrame({'Error': ['No query provided']})}
        
        try:
            df = self.db_manager.execute_query(self.query, self.params, db_name=self.db_name)
            return {'results': df}
        except Exception as e:
            return {'error': pd.DataFrame({'Error': [str(e)]})}
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {'results': 'Query Results', 'error': 'Error'}