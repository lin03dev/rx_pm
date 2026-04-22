"""
Worklog Configuration - Dynamic worklog field definitions and calculations
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class WorklogType(str, Enum):
    BIBLE = "bible"
    OBS = "obs"
    LITERATURE = "literature"
    GRAMMAR = "grammar"
    OTHER = "other"


@dataclass
class WorklogFieldGroup:
    """Group of related worklog fields for a project type"""
    project_type: str
    fields: List[str]
    label: str
    calculation_formula: Optional[str] = None  # e.g., "end_verse - start_verse + 1"
    unit: str = "items"  # verses, chapters, paragraphs, etc.


@dataclass
class WorklogSummaryMetric:
    """Metric for summarizing worklog data"""
    name: str
    label: str
    calculation: str  # sum, avg, count_distinct
    source_fields: List[str]
    format: str = "number"  # number, percentage, duration


class WorklogConfig:
    """Configuration for worklog fields and calculations"""
    
    def __init__(self):
        self.field_groups: Dict[str, WorklogFieldGroup] = {}
        self.summary_metrics: List[WorklogSummaryMetric] = []
        self.role_mappings: Dict[str, List[str]] = {}
        self._load_default_config()
    
    def _load_default_config(self):
        """Load default worklog configuration"""
        
        # Bible worklog fields
        self.field_groups["bible"] = WorklogFieldGroup(
            project_type="TEXT_TRANSLATION",
            fields=["bookNo", "startChapter", "startVerse", "endChapter", "endVerse"],
            label="Bible Translation",
            calculation_formula="(end_verse - start_verse + 1)",
            unit="verses"
        )
        
        # OBS worklog fields
        self.field_groups["obs"] = WorklogFieldGroup(
            project_type="OBS",
            fields=["obsStartChapter", "obsEndChapter", "obsStartPara", "obsEndPara"],
            label="OBS Translation",
            calculation_formula="(obs_end_para - obs_start_para + 1)",
            unit="paragraphs"
        )
        
        # Literature worklog fields
        self.field_groups["literature"] = WorklogFieldGroup(
            project_type="LITERATURE",
            fields=["literatureGenre"],
            label="Literature Translation",
            unit="genres"
        )
        
        # Grammar worklog fields (none specific, but can be added)
        self.field_groups["grammar"] = WorklogFieldGroup(
            project_type="GRAMMAR",
            fields=[],
            label="Grammar Translation",
            unit="items"
        )
        
        # Summary metrics
        self.summary_metrics = [
            WorklogSummaryMetric(
                name="total_work_days",
                label="Total Work Days",
                calculation="sum",
                source_fields=["days_worked"],
                format="number"
            ),
            WorklogSummaryMetric(
                name="total_work_sessions",
                label="Total Work Sessions",
                calculation="count",
                source_fields=["id"],
                format="number"
            ),
            WorklogSummaryMetric(
                name="total_verses_translated",
                label="Total Verses Translated",
                calculation="sum",
                source_fields=["verses_worked"],
                format="number"
            ),
            WorklogSummaryMetric(
                name="total_obs_paragraphs",
                label="Total OBS Paragraphs",
                calculation="sum",
                source_fields=["obs_paragraphs_worked"],
                format="number"
            ),
            WorklogSummaryMetric(
                name="avg_daily_productivity",
                label="Average Daily Productivity",
                calculation="avg",
                source_fields=["verses_worked", "days_worked"],
                format="number"
            )
        ]
        
        # Role mappings (which roles can do which work types)
        self.role_mappings = {
            "MTT": ["bible", "obs", "literature", "grammar"],
            "QC": ["bible", "obs", "literature"],
            "ADMIN": ["bible", "obs", "literature", "grammar"],
            "SUPER_ADMIN": ["bible", "obs", "literature", "grammar"]
        }
    
    def get_field_group(self, project_type: str) -> Optional[WorklogFieldGroup]:
        """Get field group for a project type"""
        for group in self.field_groups.values():
            if group.project_type == project_type:
                return group
        return None
    
    def get_fields_for_project_type(self, project_type: str) -> List[str]:
        """Get worklog fields used for a project type"""
        group = self.get_field_group(project_type)
        return group.fields if group else []
    
    def calculate_work_done(self, row: Dict[str, Any], project_type: str) -> int:
        """Calculate work done based on project type"""
        group = self.get_field_group(project_type)
        if not group or not group.calculation_formula:
            return 0
        
        # Simple formula evaluation
        formula = group.calculation_formula
        
        # Replace field names with values
        for field in group.fields:
            # Convert snake_case to camelCase for JSON field names
            db_field = self._to_camel_case(field)
            value = row.get(db_field, 0) or row.get(field, 0)
            formula = formula.replace(field, str(value))
            formula = formula.replace(self._to_snake_case(field), str(value))
        
        try:
            # Safe evaluation of simple arithmetic
            return int(eval(formula))
        except:
            return 0
    
    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def _to_snake_case(self, camel_str: str) -> str:
        """Convert camelCase to snake_case"""
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
    
    def get_summary_metrics(self) -> List[WorklogSummaryMetric]:
        """Get all summary metrics"""
        return self.summary_metrics
    
    def get_roles_for_work_type(self, work_type: str) -> List[str]:
        """Get roles that can perform a work type"""
        roles = []
        for role, work_types in self.role_mappings.items():
            if work_type in work_types:
                roles.append(role)
        return roles


# Singleton instance
_worklog_config = None

def get_worklog_config() -> WorklogConfig:
    """Get the singleton instance"""
    global _worklog_config
    if _worklog_config is None:
        _worklog_config = WorklogConfig()
    return _worklog_config