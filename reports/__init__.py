"""
Reports Module - Export all report classes
"""

from reports.base_report import BaseReport
from reports.user_report import UserReport
from reports.custom_report import CustomReport
from reports.individual_performance_report import IndividualPerformanceReport
from reports.lms_report import LMSReport

# Dynamic reports
try:
    from reports.consolidated_report_dynamic import ConsolidatedReportDynamic
except ImportError:
    ConsolidatedReportDynamic = None

# Legacy reports (still work)
try:
    from reports.bible_project_completion_report import BibleProjectCompletionReport
except ImportError:
    BibleProjectCompletionReport = None

try:
    from reports.obs_project_completion_report import OBSProjectCompletionReport
except ImportError:
    OBSProjectCompletionReport = None

try:
    from reports.literature_project_completion_report import LiteratureProjectCompletionReport
except ImportError:
    LiteratureProjectCompletionReport = None

try:
    from reports.grammar_project_completion_report import GrammarProjectCompletionReport
except ImportError:
    GrammarProjectCompletionReport = None

try:
    from reports.worklog_report import WorklogReport
except ImportError:
    WorklogReport = None

try:
    from reports.user_activity_report import UserActivityReport
except ImportError:
    UserActivityReport = None

try:
    from reports.user_assignment_report import UserAssignmentReport
except ImportError:
    UserAssignmentReport = None

try:
    from reports.literature_genre_report import LiteratureGenreReport
except ImportError:
    LiteratureGenreReport = None

try:
    from reports.ag_drafting_monitoring_report import AGDraftingMonitoringReport
except ImportError:
    AGDraftingMonitoringReport = None

__all__ = [
    'BaseReport',
    'UserReport',
    'CustomReport',
    'IndividualPerformanceReport',
    'LMSReport',
    'ConsolidatedReportDynamic',
    'BibleProjectCompletionReport',
    'OBSProjectCompletionReport',
    'LiteratureProjectCompletionReport',
    'GrammarProjectCompletionReport',
    'WorklogReport',
    'UserActivityReport',
    'UserAssignmentReport',
    'LiteratureGenreReport',
    'AGDraftingMonitoringReport',
]
