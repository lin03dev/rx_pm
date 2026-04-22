"""
Config module initialization - Complete dynamic configuration system
"""

from config.database_config import DatabaseConfigManager, DatabaseConfig, DatabaseType
from config.book_mapping_config import (
    BookMappingConfig, 
    get_book_mapping_config,
    map_book,
    map_verse_id,
    get_book_name
)
from config.obs_mapping_config import (
    OBSMappingConfig,
    get_obs_mapping_config,
    parse_obs_assigned_chapters,
    get_obs_chapter_name,
    get_obs_chapter_paragraph_count,
    get_obs_audio_config,
    get_obs_mtt_config
)
from config.project_type_config import (
    ProjectType,
    ProjectTypeConfig,
    ProjectTypeConfigManager,
    get_project_type_config_manager,
    get_project_type_config
)
from config.field_mapping_config import (
    FieldMapping,
    TableFieldMapping,
    FieldMappingConfig,
    get_field_mapping_config
)
from config.relationship_config import (
    Relationship,
    RelationshipGroup,
    RelationshipType,
    RelationshipConfig,
    get_relationship_config
)
from config.worklog_config import (
    WorklogFieldGroup,
    WorklogSummaryMetric,
    WorklogConfig,
    get_worklog_config
)
from config.report_templates import (
    ReportType,
    ReportColumn,
    ReportSection,
    ReportTemplate,
    ReportTemplateConfig,
    get_report_template_config
)
from config.excel_template_config import (
    TemplatePurpose,
    TemplateColumn,
    TemplateSheet,
    ExcelTemplate,
    ExcelTemplateManager,
    get_excel_template_manager
)

__all__ = [
    # Database
    'DatabaseConfigManager',
    'DatabaseConfig', 
    'DatabaseType',
    
    # Book Mapping
    'BookMappingConfig',
    'get_book_mapping_config',
    'map_book',
    'map_verse_id',
    'get_book_name',
    
    # OBS Mapping
    'OBSMappingConfig',
    'get_obs_mapping_config',
    'parse_obs_assigned_chapters',
    'get_obs_chapter_name',
    'get_obs_chapter_paragraph_count',
    'get_obs_audio_config',
    'get_obs_mtt_config',
    
    # Project Type Config
    'ProjectType',
    'ProjectTypeConfig',
    'ProjectTypeConfigManager',
    'get_project_type_config_manager',
    'get_project_type_config',
    
    # Field Mapping
    'FieldMapping',
    'TableFieldMapping',
    'FieldMappingConfig',
    'get_field_mapping_config',
    
    # Relationship Config
    'Relationship',
    'RelationshipGroup',
    'RelationshipType',
    'RelationshipConfig',
    'get_relationship_config',
    
    # Worklog Config
    'WorklogFieldGroup',
    'WorklogSummaryMetric',
    'WorklogConfig',
    'get_worklog_config',
    
    # Report Templates
    'ReportType',
    'ReportColumn',
    'ReportSection',
    'ReportTemplate',
    'ReportTemplateConfig',
    'get_report_template_config',
    
    # Excel Templates
    'TemplatePurpose',
    'TemplateColumn',
    'TemplateSheet',
    'ExcelTemplate',
    'ExcelTemplateManager',
    'get_excel_template_manager',
]