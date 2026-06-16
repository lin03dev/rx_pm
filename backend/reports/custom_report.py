"""
Custom Report - User-defined SQL reports (schema-bound to selected database).
"""

import pandas as pd
from typing import Dict, Any

from core.schema_guard import SchemaViolationError
from reports.base_report import BaseReport


class CustomReport(BaseReport):
    """Custom Report - Execute user-provided SQL against registered schema tables."""

    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.query = kwargs.get('query', '')
        self.params = kwargs.get('params', {})

    def generate(self) -> Dict[str, pd.DataFrame]:
        if not self.query.strip():
            return {'error': pd.DataFrame({'Error': ['No query provided']})}

        try:
            tables = self.schema.extract_schema_tables(self.query)
            if not tables:
                raise SchemaViolationError(
                    "Custom query must reference registered schema tables via FROM or JOIN clauses"
                )
            df = self.schema.query(self.query, tables, params=self.params)
            return {'results': df}
        except SchemaViolationError as exc:
            return {'error': pd.DataFrame({'Error': [str(exc)]})}
        except Exception as e:
            return {'error': pd.DataFrame({'Error': [str(e)]})}
    
