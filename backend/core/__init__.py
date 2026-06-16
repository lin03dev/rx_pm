"""Core reporting engine components."""

from core.database_manager import DatabaseManager
from core.report_engine import ReportEngine

try:
    from core.template_uploader import TemplateUploader
except ImportError:
    TemplateUploader = None

__all__ = [
    "DatabaseManager",
    "ReportEngine",
    "TemplateUploader",
]
