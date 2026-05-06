"""
Core module initialization - Backward compatible
"""

from core.database_manager import DatabaseManager

try:
    from core.report_engine import ReportEngine
except ImportError:
    ReportEngine = None

try:
    from core.content_analyzer import (
        ContentAnalyzer,
        ContentMetrics,
        GenericArrayAnalyzer,
        OBSChapterAnalyzer,
        LiteratureBlockAnalyzer,
        BibleChapterAnalyzer,
        AnalyzerFactory
    )
except ImportError:
    ContentAnalyzer = None
    ContentMetrics = None
    GenericArrayAnalyzer = None
    OBSChapterAnalyzer = None
    LiteratureBlockAnalyzer = None
    BibleChapterAnalyzer = None
    AnalyzerFactory = None

try:
    from core.dynamic_field_mapper import DynamicFieldMapper, get_field_mapper
except ImportError:
    DynamicFieldMapper = None
    def get_field_mapper(*args, **kwargs): return None

try:
    from core.completion_calculator import (
        CompletionCalculator,
        ProjectCompletionCalculator,
        OBSCompletionCalculator,
        CompletionStatus
    )
except ImportError:
    CompletionCalculator = None
    ProjectCompletionCalculator = None
    OBSCompletionCalculator = None
    CompletionStatus = None

try:
    from core.query_builder import QueryBuilder, AdvancedQueryBuilder, QueryTemplate
except ImportError:
    QueryBuilder = None
    AdvancedQueryBuilder = None
    QueryTemplate = None

try:
    from core.template_uploader import TemplateUploader
except ImportError:
    TemplateUploader = None


__all__ = [
    'DatabaseManager',
    'ReportEngine',
    'ContentAnalyzer',
    'ContentMetrics',
    'GenericArrayAnalyzer',
    'OBSChapterAnalyzer',
    'LiteratureBlockAnalyzer',
    'BibleChapterAnalyzer',
    'AnalyzerFactory',
    'DynamicFieldMapper',
    'get_field_mapper',
    'CompletionCalculator',
    'ProjectCompletionCalculator',
    'OBSCompletionCalculator',
    'CompletionStatus',
    'QueryBuilder',
    'AdvancedQueryBuilder',
    'QueryTemplate',
    'TemplateUploader',
]
