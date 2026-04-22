"""
Report Templates - Dynamic report generation templates
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ReportType(str, Enum):
    COMPLETION = "completion"
    PERFORMANCE = "performance"
    WORKLOG = "worklog"
    USER = "user"
    CUSTOM = "custom"


@dataclass
class ReportColumn:
    """Definition of a report column"""
    name: str
    label: str
    source: str  # table.field or calculation
    data_type: str = "string"
    format: Optional[str] = None
    width: Optional[int] = None
    visible: bool = True
    sortable: bool = True
    filterable: bool = True


@dataclass
class ReportSection:
    """A section within a report (one sheet in Excel)"""
    name: str
    label: str
    query_template: str
    columns: List[ReportColumn] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    order_by: List[str] = field(default_factory=list)
    filters: List[str] = field(default_factory=list)
    joins: List[str] = field(default_factory=list)


@dataclass
class ReportTemplate:
    """Complete report template"""
    name: str
    label: str
    report_type: ReportType
    description: str
    sections: List[ReportSection] = field(default_factory=list)
    available_filters: List[str] = field(default_factory=list)
    default_format: str = "excel"
    requires_aggregation: bool = False


class ReportTemplateConfig:
    """Configuration for report templates"""
    
    def __init__(self):
        self.templates: Dict[str, ReportTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default report templates"""
        
        # ============================================================
        # Bible Completion Report Template
        # ============================================================
        bible_completion = ReportTemplate(
            name="bible_completion",
            label="Bible Project Completion",
            report_type=ReportType.COMPLETION,
            description="Track assigned vs completed work for Bible translation projects",
            available_filters=["project_id", "user_id", "role", "country", "language"],
            sections=[
                ReportSection(
                    name="projects_overview",
                    label="All Bible Projects",
                    query_template="""
                    SELECT 
                        p.id as project_id,
                        p.name as project_name,
                        l.name as language_name,
                        c.name as country
                    FROM projects p
                    LEFT JOIN languages l ON p."languageId" = l.id
                    LEFT JOIN countries c ON p."countryId" = c.id
                    WHERE p."projectType" = 'TEXT_TRANSLATION'
                    ORDER BY p.name
                    """,
                    columns=[
                        ReportColumn("project_id", "Project ID", "projects.id"),
                        ReportColumn("project_name", "Project Name", "projects.name"),
                        ReportColumn("language_name", "Language", "languages.name"),
                        ReportColumn("country", "Country", "countries.name"),
                    ]
                ),
                ReportSection(
                    name="project_status",
                    label="Assigned vs Completed",
                    query_template="""
                    SELECT 
                        p.id as project_id,
                        p.name as project_name,
                        COUNT(DISTINCT utp."userId") as mtts_assigned,
                        COUNT(DISTINCT utp.verses) as verses_assigned
                    FROM projects p
                    LEFT JOIN users_to_projects utp ON p.id = utp."projectId" AND utp.role = 'MTT'
                    WHERE p."projectType" = 'TEXT_TRANSLATION'
                    GROUP BY p.id, p.name
                    """,
                    columns=[
                        ReportColumn("project_id", "Project ID", "projects.id"),
                        ReportColumn("project_name", "Project Name", "projects.name"),
                        ReportColumn("mtts_assigned", "MTTs Assigned", "calculation", data_type="integer"),
                        ReportColumn("verses_assigned", "Verses Assigned", "calculation", data_type="integer"),
                    ]
                )
            ]
        )
        self.templates["bible_completion"] = bible_completion
        
        # ============================================================
        # OBS Completion Report Template
        # ============================================================
        obs_completion = ReportTemplate(
            name="obs_completion",
            label="OBS Project Completion",
            report_type=ReportType.COMPLETION,
            description="Track assigned vs completed work for OBS projects with audio",
            available_filters=["project_id", "user_id", "role", "country"],
            sections=[
                ReportSection(
                    name="projects_overview",
                    label="All OBS Projects",
                    query_template="""
                    SELECT 
                        p.id as project_id,
                        p.name as project_name,
                        l.name as language_name,
                        c.name as country
                    FROM projects p
                    LEFT JOIN languages l ON p."languageId" = l.id
                    LEFT JOIN countries c ON p."countryId" = c.id
                    WHERE p."projectType" = 'OBS'
                    ORDER BY p.name
                    """
                ),
                ReportSection(
                    name="mtt_performance",
                    label="MTT Performance",
                    query_template="""
                    SELECT 
                        u.id as user_id,
                        u.username,
                        COUNT(DISTINCT utp."projectId") as projects_assigned
                    FROM users u
                    LEFT JOIN users_to_projects utp ON u.id = utp."userId" AND utp.role = 'MTT'
                    LEFT JOIN projects p ON utp."projectId" = p.id AND p."projectType" = 'OBS'
                    GROUP BY u.id, u.username
                    HAVING COUNT(DISTINCT utp."projectId") > 0
                    """
                )
            ]
        )
        self.templates["obs_completion"] = obs_completion
        
        # ============================================================
        # Literature Completion Report Template
        # ============================================================
        literature_completion = ReportTemplate(
            name="literature_completion",
            label="Literature Project Completion",
            report_type=ReportType.COMPLETION,
            description="Track assigned vs completed work for Literature projects",
            available_filters=["project_id", "user_id", "role"],
            sections=[
                ReportSection(
                    name="projects_overview",
                    label="All Literature Projects",
                    query_template="""
                    SELECT 
                        p.id as project_id,
                        p.name as project_name,
                        l.name as language_name,
                        c.name as country
                    FROM projects p
                    LEFT JOIN languages l ON p."languageId" = l.id
                    LEFT JOIN countries c ON p."countryId" = c.id
                    WHERE p."projectType" IN ('LITERATURE', 'LITERATURE_PROJECT')
                    ORDER BY p.name
                    """
                )
            ]
        )
        self.templates["literature_completion"] = literature_completion
        
        # ============================================================
        # Grammar Completion Report Template
        # ============================================================
        grammar_completion = ReportTemplate(
            name="grammar_completion",
            label="Grammar Project Completion",
            report_type=ReportType.COMPLETION,
            description="Track assigned vs completed work for Grammar projects",
            available_filters=["project_id", "user_id", "role"],
            sections=[
                ReportSection(
                    name="projects_overview",
                    label="All Grammar Projects",
                    query_template="""
                    SELECT 
                        p.id as project_id,
                        p.name as project_name,
                        p."projectType" as project_type,
                        l.name as language_name,
                        c.name as country
                    FROM projects p
                    LEFT JOIN languages l ON p."languageId" = l.id
                    LEFT JOIN countries c ON p."countryId" = c.id
                    WHERE p."projectType" IN ('GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
                    ORDER BY p."projectType", p.name
                    """
                )
            ]
        )
        self.templates["grammar_completion"] = grammar_completion
        
        # ============================================================
        # Individual Performance Report Template
        # ============================================================
        individual_performance = ReportTemplate(
            name="individual_performance",
            label="Individual Performance",
            report_type=ReportType.PERFORMANCE,
            description="Track assigned vs completed work per person across all project types",
            available_filters=["user_id", "username", "role", "country", "language"],
            requires_aggregation=True,
            sections=[
                ReportSection(
                    name="individual_summary",
                    label="Individual Summary",
                    query_template="""
                    SELECT 
                        u.id as user_id,
                        u.username,
                        u.email,
                        u.role::text as user_role,
                        p."firstName",
                        p."lastName",
                        c.name as country
                    FROM users u
                    LEFT JOIN person p ON u."personId"::text = p.id
                    LEFT JOIN countries c ON p."countryId" = c.id
                    WHERE u.role::text != 'SUPER_ADMIN'
                    ORDER BY c.name, p."firstName", p."lastName"
                    """
                )
            ]
        )
        self.templates["individual_performance"] = individual_performance
        
        # ============================================================
        # Worklog Report Template
        # ============================================================
        worklog_report = ReportTemplate(
            name="worklog",
            label="Worklog Report",
            report_type=ReportType.WORKLOG,
            description="Track work sessions and productivity",
            available_filters=["role", "stage", "software", "project_type"],
            sections=[
                ReportSection(
                    name="worklog_details",
                    label="Worklog Details",
                    query_template="""
                    SELECT 
                        w.id,
                        w."projectId",
                        p.name as project_name,
                        p."projectType" as project_type,
                        w.role,
                        w."userId",
                        u.username,
                        w."startDate",
                        w."endDate",
                        w.description,
                        w."translationSoftware",
                        w.stage,
                        w."noWork"
                    FROM worklogs w
                    LEFT JOIN users u ON w."userId" = u.id
                    LEFT JOIN projects p ON w."projectId" = p.id
                    WHERE 1=1
                    ORDER BY w."startDate" DESC
                    LIMIT 5000
                    """
                )
            ]
        )
        self.templates["worklog"] = worklog_report
        
        # ============================================================
        # User Report Template
        # ============================================================
        user_report = ReportTemplate(
            name="user",
            label="User Report",
            report_type=ReportType.USER,
            description="User management and assignments",
            available_filters=["role", "country"],
            sections=[
                ReportSection(
                    name="user_details",
                    label="User Details",
                    query_template="""
                    SELECT 
                        u.id as user_id,
                        u.username,
                        u.email,
                        u.role::text as user_role,
                        u.name as display_name,
                        u."createdAt",
                        p."firstName",
                        p."lastName",
                        c.name as country
                    FROM users u
                    LEFT JOIN person p ON u."personId"::text = p.id
                    LEFT JOIN countries c ON p."countryId" = c.id
                    WHERE 1=1
                    ORDER BY c.name, u.username
                    """
                )
            ]
        )
        self.templates["user"] = user_report
    
    def get_template(self, name: str) -> Optional[ReportTemplate]:
        """Get a report template by name"""
        return self.templates.get(name)
    
    def get_all_templates(self) -> Dict[str, ReportTemplate]:
        """Get all report templates"""
        return self.templates
    
    def build_query_from_template(self, template_name: str, section_name: str, 
                                   filters: Dict[str, Any] = None) -> str:
        """Build a SQL query from a template section"""
        template = self.get_template(template_name)
        if not template:
            return ""
        
        section = None
        for s in template.sections:
            if s.name == section_name:
                section = s
                break
        
        if not section:
            return ""
        
        query = section.query_template
        
        # Apply filters
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f'"{key}" = \'{value}\'')
                else:
                    where_clauses.append(f'"{key}" = {value}')
            
            if where_clauses:
                if 'WHERE 1=1' in query:
                    query = query.replace('WHERE 1=1', f'WHERE 1=1 AND {" AND ".join(where_clauses)}')
                elif 'WHERE' in query:
                    query += f' AND {" AND ".join(where_clauses)}'
                else:
                    query += f' WHERE {" AND ".join(where_clauses)}'
        
        return query


# Singleton instance
_report_template_config = None

def get_report_template_config() -> ReportTemplateConfig:
    """Get the singleton instance"""
    global _report_template_config
    if _report_template_config is None:
        _report_template_config = ReportTemplateConfig()
    return _report_template_config