"""
Base Report V3 - Dynamic base class with dialect/ROLV support
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set, Union, Tuple
import pandas as pd
from datetime import datetime

from core.database_manager import DatabaseManager
from core.content_analyzer import ContentAnalyzer, AnalyzerFactory, ContentMetrics
from core.dynamic_field_mapper import get_field_mapper
from core.completion_calculator import CompletionCalculator, CompletionStatus
from config.dynamic_config import get_dynamic_config
from config.dialect_config import get_dialect_manager, DialectInfo
from core.schema_guard import SchemaGuard, SchemaViolationError
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseReportV3(ABC):
    """Dynamic base report with content analysis, field mapping, and dialect support"""
    
    def __init__(self, db_manager: DatabaseManager, **kwargs):
        self.db_manager = db_manager
        self.filters = kwargs.get('filters', {})
        self.db_name = kwargs.get('db_name')
        self.report_id = kwargs.get('report_id')
        self.params = kwargs
        self.config = get_dynamic_config()
        self.field_mapper = get_field_mapper()
        self.completion_calculator = CompletionCalculator(db_manager)
        self.dialect_manager = get_dialect_manager(db_manager)
        self.schema = SchemaGuard(db_manager, self.db_name, self.report_id)
        if self.db_name and self.report_id:
            self.schema.validate_primary_connection()
        
        # Cache for project configs
        self._project_configs: Dict[str, Dict] = {}
        self.available_filters = []
        
        # Dialect inclusion flag - override in child reports if needed
        self.include_null_dialects = True
        self._apply_schema_catalog()
        
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

    def schema_query(self, query: str, tables: List[str], params: Optional[Dict] = None) -> pd.DataFrame:
        """Execute a query constrained to registered schema tables."""
        return self.schema.query(query, tables, params=params)

    def schema_message(self, message: str) -> pd.DataFrame:
        return self.schema.message_frame(message)

    def companion_schema_query(
        self,
        target_system: str,
        query: str,
        tables: List[str],
        params: Optional[Dict] = None,
    ) -> pd.DataFrame:
        """Run a query on an allowed companion database (cross-db reports only)."""
        return self.schema.companion_query(target_system, query, tables, params=params)
    
    def get_project_config(self, project_type: str) -> Dict[str, Any]:
        """Get configuration for a project type"""
        if project_type not in self._project_configs:
            all_configs = self.config.get_project_type_configs()
            self._project_configs[project_type] = all_configs.get(project_type, {})
        return self._project_configs[project_type]
    
    def get_analyzer(self, project_type: str) -> ContentAnalyzer:
        """Get content analyzer for project type"""
        config = self.get_project_config(project_type)
        analyzer_type = config.get('analyzer', 'generic_array')
        
        if analyzer_type == 'generic_array':
            item_key = config.get('item_key', 'content')
            return AnalyzerFactory.get_analyzer(project_type, {'item_key': item_key})
        
        return AnalyzerFactory.get_analyzer(project_type)
    
    def analyze_content(self, content: Any, project_type: str) -> ContentMetrics:
        """Analyze content using appropriate analyzer"""
        analyzer = self.get_analyzer(project_type)
        return analyzer.analyze(content)
    
    def get_completion_status(self, completion_pct: float, has_mtt: bool = True) -> str:
        """Get human-readable completion status"""
        status = self.completion_calculator.get_status(completion_pct, has_mtt)
        return self.completion_calculator.get_status_label(status)
    
    def get_performance_rating(self, completion_pct: float) -> str:
        """Get performance rating"""
        rating = self.completion_calculator.get_performance_rating(completion_pct)
        return rating['label']
    
    def get_mtt_names_for_project(self, project_id: str) -> tuple:
        """Get MTT names for a project"""
        query = f"""
        SELECT DISTINCT 
            COALESCE(NULLIF(u.name, ''), u.username) as mtt_name
        FROM users_to_projects utp
        JOIN users u ON utp."userId" = u.id
        WHERE utp."projectId" = '{project_id}'
          AND utp.role = 'MTT'
        ORDER BY mtt_name
        """
        try:
            df = self.execute_query(query)
            names = df['mtt_name'].tolist() if not df.empty else []
            return len(names), ', '.join(names)
        except:
            return 0, ''
    
    def get_mtt_names_for_language_dialect(self, language: str, dialect_name: str = None) -> str:
        """Get MTT names for a language-dialect combination using dialect manager"""
        mtts = self.dialect_manager.get_mtts_for_language_dialect(language, dialect_name)
        return ', '.join(mtts)
    
    def get_all_language_dialect_combinations(self, country_filter: str = None, language_filter: str = None) -> pd.DataFrame:
        """Get all language-dialect combinations including NULL dialect"""
        return self.dialect_manager.get_language_dialect_combinations(country_filter, language_filter)
    
    def normalize_record(self, table_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize record using field mapper"""
        return self.field_mapper.normalize_record(table_name, record)
    
    def safe_parse_json(self, content: Any) -> Optional[Dict]:
        """Safely parse JSON content"""
        if content is None:
            return None
        try:
            import json
            if isinstance(content, str):
                return json.loads(content)
            return content
        except:
            return None
    
    def format_date(self, date_value: Any, format_str: str = '%Y-%m-%d') -> str:
        """Format date value safely"""
        if pd.isna(date_value) or date_value is None:
            return ''
        try:
            if isinstance(date_value, str):
                return date_value[:10]
            if hasattr(date_value, 'strftime'):
                return date_value.strftime(format_str)
            return str(date_value)[:10]
        except:
            return ''
    
    def get_all_projects(self, project_types: List[str] = None, include_dialect_info: bool = True) -> pd.DataFrame:
        """Get all projects with basic info and optional dialect information"""
        type_filter = ''
        if project_types:
            types = "', '".join(project_types)
            type_filter = f"AND p.\"projectType\" IN ('{types}')"
        
        if include_dialect_info:
            query = f"""
            SELECT 
                p.id as project_id,
                p.name as project_name,
                p."projectType" as project_type,
                l.name as language_name,
                l."isoCode" as language_code,
                c.name as country,
                d.id as dialect_id,
                COALESCE(d.name, '') as dialect_name,
                COALESCE(d."rolvCode", '') as rolv_code
            FROM projects p
            LEFT JOIN languages l ON p."languageId" = l.id
            LEFT JOIN countries c ON p."countryId" = c.id
            LEFT JOIN dialects d ON p."dialectId" = d.id
            WHERE 1=1
            {type_filter}
            ORDER BY p."projectType", p.name
            """
        else:
            query = f"""
            SELECT 
                p.id as project_id,
                p.name as project_name,
                p."projectType" as project_type,
                l.name as language_name,
                l."isoCode" as language_code,
                c.name as country
            FROM projects p
            LEFT JOIN languages l ON p."languageId" = l.id
            LEFT JOIN countries c ON p."countryId" = c.id
            WHERE 1=1
            {type_filter}
            ORDER BY p."projectType", p.name
            """
        return self.execute_query(query)
    
    def get_projects_by_language_dialect(self, language: str, dialect_name: str = None) -> pd.DataFrame:
        """Get projects for a specific language-dialect combination"""
        lang_escaped = language.replace("'", "''")
        
        if dialect_name:
            dialect_escaped = dialect_name.replace("'", "''")
            query = f"""
            SELECT 
                p.id as project_id,
                p.name as project_name,
                p."projectType" as project_type
            FROM projects p
            JOIN languages l ON p."languageId" = l.id
            LEFT JOIN dialects d ON p."dialectId" = d.id
            WHERE l.name = '{lang_escaped}'
              AND d.name = '{dialect_escaped}'
            """
        else:
            query = f"""
            SELECT 
                p.id as project_id,
                p.name as project_name,
                p."projectType" as project_type
            FROM projects p
            JOIN languages l ON p."languageId" = l.id
            WHERE l.name = '{lang_escaped}'
              AND (p."dialectId" IS NULL OR p."dialectId" = '')
            """
        
        return self.execute_query(query)
    
    def get_mtt_assignments(self, project_type: str = None, include_dialect_info: bool = True) -> pd.DataFrame:
        """Get MTT assignments with optional dialect information"""
        type_filter = ''
        if project_type:
            type_filter = f"AND p.\"projectType\" = '{project_type}'"
        
        if include_dialect_info:
            query = f"""
            SELECT 
                utp."projectId",
                p.name as project_name,
                p."projectType" as project_type,
                l.name as language_name,
                l."isoCode" as language_code,
                c.name as country,
                COALESCE(d.name, '') as dialect_name,
                COALESCE(d."rolvCode", '') as rolv_code,
                u.id as user_id,
                u.username,
                COALESCE(NULLIF(u.name, ''), u.username) as full_name,
                u.email,
                utp.verses,
                utp."obsChapters",
                utp."literatureGenres",
                utp.role as project_role
            FROM users_to_projects utp
            LEFT JOIN projects p ON utp."projectId" = p.id
            LEFT JOIN languages l ON p."languageId" = l.id
            LEFT JOIN countries c ON p."countryId" = c.id
            LEFT JOIN dialects d ON p."dialectId" = d.id
            LEFT JOIN users u ON utp."userId" = u.id
            WHERE utp.role = 'MTT'
            {type_filter}
            ORDER BY p.name, u.username
            """
        else:
            query = f"""
            SELECT 
                utp."projectId",
                p.name as project_name,
                p."projectType" as project_type,
                l.name as language_name,
                l."isoCode" as language_code,
                c.name as country,
                u.id as user_id,
                u.username,
                COALESCE(NULLIF(u.name, ''), u.username) as full_name,
                u.email,
                utp.verses,
                utp."obsChapters",
                utp."literatureGenres",
                utp.role as project_role
            FROM users_to_projects utp
            LEFT JOIN projects p ON utp."projectId" = p.id
            LEFT JOIN languages l ON p."languageId" = l.id
            LEFT JOIN countries c ON p."countryId" = c.id
            LEFT JOIN users u ON utp."userId" = u.id
            WHERE utp.role = 'MTT'
            {type_filter}
            ORDER BY p.name, u.username
            """
        return self.execute_query(query)
    
    def get_assigned_items(self, project_id: str, assignment_field: str) -> Set[str]:
        """Get assigned items for a project"""
        query = f"""
        SELECT DISTINCT trim(unnest(string_to_array(COALESCE({assignment_field}, ''), ','))) as item
        FROM users_to_projects
        WHERE "projectId" = '{project_id}'
          AND role = 'MTT'
          AND {assignment_field} IS NOT NULL
        """
        try:
            df = self.execute_query(query)
            return set(df['item'].tolist()) if not df.empty else set()
        except:
            return set()
    
    def calculate_completion_percentage(self, assigned: int, completed: int) -> float:
        """Calculate completion percentage"""
        if assigned == 0:
            return 0.0
        return min((completed / assigned) * 100, 100.0)
    
    def get_summary_stats(self, data: pd.DataFrame, metrics: List[str]) -> pd.DataFrame:
        """Generate summary statistics from data"""
        summary = []
        
        for metric in metrics:
            if metric in data.columns:
                if data[metric].dtype in ['int64', 'float64']:
                    summary.append({
                        'Metric': metric.replace('_', ' ').title(),
                        'Value': data[metric].sum()
                    })
                else:
                    summary.append({
                        'Metric': metric.replace('_', ' ').title(),
                        'Value': data[metric].nunique()
                    })
        
        return pd.DataFrame(summary)
    
    def sanitize_sheet_name(self, name: str) -> str:
        """Sanitize sheet name for Excel (max 31 chars)"""
        invalid_chars = ['[', ']', ':', '*', '?', '/', '\\']
        for char in invalid_chars:
            name = name.replace(char, '')
        return name[:31]
    
    def clear_caches(self):
        """Clear all caches including dialect cache"""
        self.dialect_manager.clear_cache()
        self._project_configs.clear()
