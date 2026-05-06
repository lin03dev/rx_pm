"""
Config module initialization - Backward compatible with both old and new systems
"""

# ============================================================
# Database Config (Always needed)
# ============================================================
from config.database_config import DatabaseConfigManager, DatabaseConfig, DatabaseType

# ============================================================
# New Dynamic Config (Primary)
# ============================================================
from config.dynamic_config import DynamicConfig, get_dynamic_config

# ============================================================
# Backward Compatibility - Try to import old modules, but don't fail
# ============================================================
try:
    from config.book_mapping_config import (
        BookMappingConfig, 
        get_book_mapping_config,
        map_book,
        map_verse_id,
        get_book_name
    )
except ImportError:
    # Provide fallback functions
    def get_book_mapping_config(*args, **kwargs):
        from config.dynamic_config import get_dynamic_config
        return get_dynamic_config().get_book_mappings()
    
    def map_book(book_num):
        # Simple mapping for backward compatibility
        if 101 <= book_num <= 166:
            return book_num - 100
        elif 240 <= book_num <= 266:
            return book_num - 200
        return book_num
    
    def map_verse_id(verse_id):
        if len(verse_id) >= 9:
            book = int(verse_id[:3])
            mapped_book = map_book(book)
            return f"{mapped_book:03d}{verse_id[3:6]}{verse_id[6:9]}"
        return verse_id
    
    def get_book_name(book_num):
        names = {1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
                 6: "Joshua", 7: "Judges", 8: "Ruth", 9: "1 Samuel", 10: "2 Samuel",
                 11: "1 Kings", 12: "2 Kings", 13: "1 Chronicles", 14: "2 Chronicles",
                 15: "Ezra", 16: "Nehemiah", 17: "Esther", 18: "Job", 19: "Psalms",
                 20: "Proverbs", 21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah",
                 24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel",
                 28: "Hosea", 29: "Joel", 30: "Amos", 31: "Obadiah", 32: "Jonah",
                 33: "Micah", 34: "Nahum", 35: "Habakkuk", 36: "Zephaniah", 37: "Haggai",
                 38: "Zechariah", 39: "Malachi", 40: "Matthew", 41: "Mark", 42: "Luke",
                 43: "John", 44: "Acts", 45: "Romans", 46: "1 Corinthians", 47: "2 Corinthians",
                 48: "Galatians", 49: "Ephesians", 50: "Philippians", 51: "Colossians",
                 52: "1 Thessalonians", 53: "2 Thessalonians", 54: "1 Timothy", 55: "2 Timothy",
                 56: "Titus", 57: "Philemon", 58: "Hebrews", 59: "James", 60: "1 Peter",
                 61: "2 Peter", 62: "1 John", 63: "2 John", 64: "3 John", 65: "Jude", 66: "Revelation"}
        return names.get(book_num, f"Book {book_num}")
    
    BookMappingConfig = None
    get_book_mapping_config = get_book_mapping_config
    map_book = map_book
    map_verse_id = map_verse_id
    get_book_name = get_book_name

try:
    from config.obs_mapping_config import (
        OBSMappingConfig,
        get_obs_mapping_config,
        parse_obs_assigned_chapters,
        get_obs_chapter_name,
        get_obs_chapter_paragraph_count,
        get_obs_audio_config,
        get_obs_mtt_config
    )
except ImportError:
    # Provide fallback functions
    def get_obs_mapping_config(*args, **kwargs):
        from config.dynamic_config import get_dynamic_config
        return get_dynamic_config().get_obs_config()
    
    def parse_obs_assigned_chapters(chapters_string):
        result = set()
        if not chapters_string:
            return result
        for ch in chapters_string.split(','):
            ch = ch.strip()
            if ch and ch.isdigit():
                result.add(int(ch))
        return result
    
    def get_obs_chapter_name(chapter_no):
        names = {1: "The Creation", 2: "Sin Enters the World", 3: "The Flood",
                 4: "God's Covenant with Abraham", 5: "The Son of Promise"}
        return names.get(chapter_no, f"Chapter {chapter_no}")
    
    def get_obs_chapter_paragraph_count(chapter_no):
        counts = {1: 16, 2: 12, 3: 16, 4: 9, 5: 12}
        return counts.get(chapter_no, 10)
    
    def get_obs_audio_config():
        return {'types': ['title', 'para'], 'title_required': True, 'para_audio_required': True}
    
    def get_obs_mtt_config():
        return {'status_rules': {'completed': {'min_completion': 100}, 'in_progress': {'min_completion': 1}}}
    
    OBSMappingConfig = None
    get_obs_mapping_config = get_obs_mapping_config
    parse_obs_assigned_chapters = parse_obs_assigned_chapters
    get_obs_chapter_name = get_obs_chapter_name
    get_obs_chapter_paragraph_count = get_obs_chapter_paragraph_count
    get_obs_audio_config = get_obs_audio_config
    get_obs_mtt_config = get_obs_mtt_config

try:
    from config.project_type_config import (
        ProjectType,
        ProjectTypeConfig,
        ProjectTypeConfigManager,
        get_project_type_config_manager,
        get_project_type_config
    )
except ImportError:
    ProjectType = None
    ProjectTypeConfig = None
    ProjectTypeConfigManager = None
    def get_project_type_config_manager(*args, **kwargs): return None
    def get_project_type_config(*args, **kwargs): return None

try:
    from config.field_mapping_config import (
        FieldMapping,
        TableFieldMapping,
        FieldMappingConfig,
        get_field_mapping_config
    )
except ImportError:
    FieldMapping = None
    TableFieldMapping = None
    FieldMappingConfig = None
    def get_field_mapping_config(*args, **kwargs): return None

try:
    from config.relationship_config import (
        Relationship,
        RelationshipGroup,
        RelationshipType,
        RelationshipConfig,
        get_relationship_config
    )
except ImportError:
    Relationship = None
    RelationshipGroup = None
    RelationshipType = None
    RelationshipConfig = None
    def get_relationship_config(*args, **kwargs): return None

try:
    from config.worklog_config import (
        WorklogFieldGroup,
        WorklogSummaryMetric,
        WorklogConfig,
        get_worklog_config
    )
except ImportError:
    WorklogFieldGroup = None
    WorklogSummaryMetric = None
    WorklogConfig = None
    def get_worklog_config(*args, **kwargs): return None

try:
    from config.report_templates import (
        ReportType,
        ReportColumn,
        ReportSection,
        ReportTemplate,
        ReportTemplateConfig,
        get_report_template_config
    )
except ImportError:
    ReportType = None
    ReportColumn = None
    ReportSection = None
    ReportTemplate = None
    ReportTemplateConfig = None
    def get_report_template_config(*args, **kwargs): return None

# ============================================================
# Excel Templates (Always needed)
# ============================================================
try:
    from config.excel_template_config import (
        TemplatePurpose,
        TemplateColumn,
        TemplateSheet,
        ExcelTemplate,
        ExcelTemplateManager,
        get_excel_template_manager
    )
except ImportError:
    TemplatePurpose = None
    TemplateColumn = None
    TemplateSheet = None
    ExcelTemplate = None
    ExcelTemplateManager = None
    def get_excel_template_manager(*args, **kwargs): return None


__all__ = [
    # Database
    'DatabaseConfigManager',
    'DatabaseConfig', 
    'DatabaseType',
    
    # New Dynamic Config
    'DynamicConfig',
    'get_dynamic_config',
    
    # Book Mapping (with fallbacks)
    'BookMappingConfig',
    'get_book_mapping_config',
    'map_book',
    'map_verse_id',
    'get_book_name',
    
    # OBS Mapping (with fallbacks)
    'OBSMappingConfig',
    'get_obs_mapping_config',
    'parse_obs_assigned_chapters',
    'get_obs_chapter_name',
    'get_obs_chapter_paragraph_count',
    'get_obs_audio_config',
    'get_obs_mtt_config',
    
    # Others (may be None if not available)
    'ProjectType',
    'ProjectTypeConfig',
    'ProjectTypeConfigManager',
    'get_project_type_config_manager',
    'get_project_type_config',
    'FieldMapping',
    'TableFieldMapping',
    'FieldMappingConfig',
    'get_field_mapping_config',
    'Relationship',
    'RelationshipGroup',
    'RelationshipType',
    'RelationshipConfig',
    'get_relationship_config',
    'WorklogFieldGroup',
    'WorklogSummaryMetric',
    'WorklogConfig',
    'get_worklog_config',
    'ReportType',
    'ReportColumn',
    'ReportSection',
    'ReportTemplate',
    'ReportTemplateConfig',
    'get_report_template_config',
    'TemplatePurpose',
    'TemplateColumn',
    'TemplateSheet',
    'ExcelTemplate',
    'ExcelTemplateManager',
    'get_excel_template_manager',
]
