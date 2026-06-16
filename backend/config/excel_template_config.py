"""
Excel Template Configuration - Dynamic Excel template generation for data import
Includes AG_Dev and Telios_LMS templates
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json


class TemplatePurpose(str, Enum):
    """Purpose of the Excel template"""
    # AG_Dev Templates
    USER_IMPORT = "user_import"
    PROJECT_IMPORT = "project_import"
    ASSIGNMENT_IMPORT = "assignment_import"
    WORKLOG_IMPORT = "worklog_import"
    BIBLE_CHAPTER_IMPORT = "bible_chapter_import"
    OBS_CHAPTER_IMPORT = "obs_chapter_import"
    LITERATURE_GENRE_IMPORT = "literature_genre_import"
    GRAMMAR_IMPORT = "grammar_import"
    
    # Telios_LMS Templates
    BATCH_CREATION = "batch_creation"
    STUDENT_ENROLLMENT = "student_enrollment"
    BATCH_MODULE = "batch_module"
    ATTENDANCE = "attendance"
    ASSIGNMENT_SUBMISSION = "assignment_submission"
    SURVEY_RESPONSE = "survey_response"
    BULK_UPDATE = "bulk_update"
    REPORT_EXPORT = "report_export"


class FieldType(str, Enum):
    """Field types for Excel columns"""
    TEXT = "text"
    NUMBER = "number"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    EMAIL = "email"
    PHONE = "phone"
    UUID = "uuid"
    ENUM = "enum"
    JSON = "json"
    MULTI_SELECT = "multi_select"
    VERSES = "verses"
    OBS_CHAPTERS = "obs_chapters"
    LITERATURE_GENRES = "literature_genres"


class ValidationType(str, Enum):
    """Validation types for Excel dropdowns"""
    LIST = "list"
    NUMBER_RANGE = "number_range"
    DATE_RANGE = "date_range"
    TEXT_LENGTH = "text_length"
    REGEX = "regex"
    CUSTOM = "custom"


@dataclass
class DropdownOption:
    """Option for dropdown list"""
    value: str
    label: str
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ColumnValidation:
    """Validation rules for a column"""
    validation_type: ValidationType
    options: Optional[List[DropdownOption]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex_pattern: Optional[str] = None
    custom_formula: Optional[str] = None
    error_message: str = "Invalid value"
    allow_blank: bool = False


@dataclass
class TemplateColumn:
    """Definition of a column in the Excel template"""
    field_name: str
    display_name: str
    field_type: FieldType
    width: int = 20
    required: bool = False
    validation: Optional[ColumnValidation] = None
    default_value: Any = None
    description: str = ""
    example: str = ""
    mapping_to_db: Optional[str] = None
    transform_function: Optional[str] = None
    group: Optional[str] = None
    order: int = 999


@dataclass
class TemplateSheet:
    """Definition of a sheet in the Excel template"""
    sheet_name: str
    purpose: TemplatePurpose
    description: str
    columns: List[TemplateColumn]
    table_name: Optional[str] = None
    primary_key_fields: List[str] = field(default_factory=list)
    update_mode: str = "insert"
    batch_size: int = 100
    pre_upload_sql: Optional[str] = None
    post_upload_sql: Optional[str] = None
    example_row: Optional[Dict[str, Any]] = None


@dataclass
class ExcelTemplate:
    """Complete Excel template definition"""
    name: str
    display_name: str
    purpose: TemplatePurpose
    description: str
    version: str = "1.0"
    sheets: List[TemplateSheet] = field(default_factory=list)
    global_validations: List[ColumnValidation] = field(default_factory=list)
    instructions: str = ""
    requires_approval: bool = False


# ============================================================
# Dropdown Data Sources
# ============================================================

class DropdownDataSources:
    """Dynamic dropdown data sources that query the database"""
    
    @staticmethod
    def get_user_roles() -> List[DropdownOption]:
        return [
            DropdownOption("MTT", "Mother Tongue Translator"),
            DropdownOption("QC", "Quality Checker"),
            DropdownOption("ADMIN", "Administrator"),
            DropdownOption("SUPER_ADMIN", "Super Administrator"),
            DropdownOption("ICT", "ICT Support"),
        ]
    
    @staticmethod
    def get_project_types() -> List[DropdownOption]:
        return [
            DropdownOption("TEXT_TRANSLATION", "Bible Translation"),
            DropdownOption("OBS", "Open Bible Stories"),
            DropdownOption("LITERATURE", "Literature Translation"),
            DropdownOption("LITERATURE_PROJECT", "Literature Project"),
            DropdownOption("GRAMMAR_PHRASES", "Grammar - Phrases"),
            DropdownOption("GRAMMAR_PRONOUNS", "Grammar - Pronouns"),
            DropdownOption("GRAMMAR_CONNECTIVES", "Grammar - Connectives"),
        ]
    
    @staticmethod
    def get_project_stages() -> List[DropdownOption]:
        return [
            DropdownOption("PLANNING", "Planning"),
            DropdownOption("IN_PROGRESS", "In Progress"),
            DropdownOption("REVIEW", "Under Review"),
            DropdownOption("COMPLETED", "Completed"),
            DropdownOption("ARCHIVED", "Archived"),
        ]
    
    @staticmethod
    def get_work_roles() -> List[DropdownOption]:
        return [
            DropdownOption("MTT", "Translator"),
            DropdownOption("QC", "Quality Checker"),
            DropdownOption("REVIEWER", "Reviewer"),
        ]
    
    @staticmethod
    def get_translation_software() -> List[DropdownOption]:
        return [
            DropdownOption("AUTOGRAPHA", "Autographa"),
            DropdownOption("PARATEXT", "ParaText"),
            DropdownOption("OTHERS", "Others"),
        ]
    
    @staticmethod
    def get_grammar_types() -> List[DropdownOption]:
        return [
            DropdownOption("GRAMMAR_PHRASES", "Phrases"),
            DropdownOption("GRAMMAR_PRONOUNS", "Pronouns"),
            DropdownOption("GRAMMAR_CONNECTIVES", "Connectives"),
        ]
    
    @staticmethod
    def get_literature_genres() -> List[DropdownOption]:
        return [
            DropdownOption("GEN001", "Bible Story"),
            DropdownOption("GEN002", "Testimonial"),
            DropdownOption("GEN003", "Teaching"),
            DropdownOption("GEN004", "Song/Poem"),
            DropdownOption("GEN005", "Drama"),
            DropdownOption("GEN006", "Article"),
        ]
    
    @staticmethod
    def get_boolean_options() -> List[DropdownOption]:
        return [
            DropdownOption("true", "Yes"),
            DropdownOption("false", "No"),
        ]
    
    @staticmethod
    def get_gender_options() -> List[DropdownOption]:
        return [
            DropdownOption("MALE", "Male"),
            DropdownOption("FEMALE", "Female"),
            DropdownOption("OTHER", "Other"),
            DropdownOption("PREFER_NOT_TO_SAY", "Prefer not to say"),
        ]
    
    # LMS Dropdowns
    @staticmethod
    def get_batch_status_options() -> List[DropdownOption]:
        return [
            DropdownOption("PLANNING", "Planning"),
            DropdownOption("ACTIVE", "Active/In Progress"),
            DropdownOption("COMPLETED", "Completed"),
            DropdownOption("CANCELLED", "Cancelled"),
            DropdownOption("ON_HOLD", "On Hold"),
        ]
    
    @staticmethod
    def get_lms_roles() -> List[DropdownOption]:
        return [
            DropdownOption("MTT", "Mother Tongue Translator"),
            DropdownOption("ICT", "ICT Support"),
            DropdownOption("QC", "Quality Checker"),
            DropdownOption("TRAINER", "Trainer"),
            DropdownOption("ADMIN", "Administrator"),
            DropdownOption("STUDENT", "Student"),
        ]
    
    @staticmethod
    def get_attendance_status() -> List[DropdownOption]:
        return [
            DropdownOption("PRESENT", "Present"),
            DropdownOption("ABSENT", "Absent"),
            DropdownOption("LATE", "Late"),
            DropdownOption("EXCUSED", "Excused"),
            DropdownOption("HALF_DAY", "Half Day"),
        ]
    
    @staticmethod
    def get_submission_status() -> List[DropdownOption]:
        return [
            DropdownOption("1", "Submitted"),
            DropdownOption("2", "Redo Required"),
            DropdownOption("3", "Approved"),
            DropdownOption("4", "Rejected"),
        ]
    
    @staticmethod
    def get_completion_status() -> List[DropdownOption]:
        return [
            DropdownOption("ENROLLED", "Enrolled"),
            DropdownOption("IN_PROGRESS", "In Progress"),
            DropdownOption("COMPLETED", "Completed"),
            DropdownOption("DROPPED", "Dropped"),
            DropdownOption("ON_LEAVE", "On Leave"),
        ]


# ============================================================
# AG_Dev Template Definitions
# ============================================================

def get_user_import_template() -> ExcelTemplate:
    """Template for importing/updating users"""
    
    sheets = [
        TemplateSheet(
            sheet_name="Users",
            purpose=TemplatePurpose.USER_IMPORT,
            description="Import or update user information",
            table_name="users",
            primary_key_fields=["id", "username"],
            update_mode="upsert",
            columns=[
                TemplateColumn(
                    field_name="id", display_name="User ID (UUID)", field_type=FieldType.UUID,
                    width=36, required=False, description="Leave empty for new users",
                    mapping_to_db="id", order=1
                ),
                TemplateColumn(
                    field_name="username", display_name="Username *", field_type=FieldType.TEXT,
                    width=20, required=True,
                    validation=ColumnValidation(validation_type=ValidationType.TEXT_LENGTH,
                        min_length=3, max_length=50, error_message="Username must be 3-50 characters"),
                    description="Unique username for login", example="john_doe",
                    mapping_to_db="username", order=2
                ),
                TemplateColumn(
                    field_name="email", display_name="Email *", field_type=FieldType.EMAIL,
                    width=30, required=True, description="Valid email address",
                    example="john@example.com", mapping_to_db="email", order=3
                ),
                TemplateColumn(
                    field_name="role", display_name="Role *", field_type=FieldType.ENUM,
                    width=15, required=True,
                    validation=ColumnValidation(validation_type=ValidationType.LIST,
                        options=DropdownDataSources.get_user_roles()),
                    mapping_to_db="role", order=4
                ),
                TemplateColumn(
                    field_name="firstName", display_name="First Name", field_type=FieldType.TEXT,
                    width=15, required=False, mapping_to_db="firstName", order=5
                ),
                TemplateColumn(
                    field_name="lastName", display_name="Last Name", field_type=FieldType.TEXT,
                    width=15, required=False, mapping_to_db="lastName", order=6
                ),
                TemplateColumn(
                    field_name="gender", display_name="Gender", field_type=FieldType.ENUM,
                    width=15, required=False,
                    validation=ColumnValidation(validation_type=ValidationType.LIST,
                        options=DropdownDataSources.get_gender_options()),
                    mapping_to_db="gender", order=7
                ),
                TemplateColumn(
                    field_name="phone", display_name="Phone", field_type=FieldType.PHONE,
                    width=15, required=False, mapping_to_db="phone", order=8
                ),
                TemplateColumn(
                    field_name="country", display_name="Country", field_type=FieldType.TEXT,
                    width=20, required=False, mapping_to_db="countryId",
                    transform_function="lookup_country_id", order=9
                ),
                TemplateColumn(
                    field_name="state", display_name="State/Region", field_type=FieldType.TEXT,
                    width=20, required=False, mapping_to_db="state", order=10
                ),
                TemplateColumn(
                    field_name="isActive", display_name="Active", field_type=FieldType.BOOLEAN,
                    width=10, required=False, default_value="true",
                    validation=ColumnValidation(validation_type=ValidationType.LIST,
                        options=DropdownDataSources.get_boolean_options()),
                    mapping_to_db="isActive", order=11
                ),
            ],
            example_row={
                "id": "", "username": "john_doe", "email": "john@example.com",
                "role": "MTT", "firstName": "John", "lastName": "Doe",
                "gender": "MALE", "phone": "+1234567890", "country": "India",
                "state": "Karnataka", "isActive": "true"
            }
        )
    ]
    
    return ExcelTemplate(
        name="user_import", display_name="User Import Template",
        purpose=TemplatePurpose.USER_IMPORT,
        description="Import or update user information in the system",
        version="1.0", sheets=sheets,
        instructions="Fields marked with * are required. Leave ID empty for new users.",
        requires_approval=True
    )


def get_project_import_template() -> ExcelTemplate:
    """Template for importing/updating projects"""
    
    sheets = [
        TemplateSheet(
            sheet_name="Projects", purpose=TemplatePurpose.PROJECT_IMPORT,
            description="Import or update project information",
            table_name="projects", primary_key_fields=["id", "name"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="id", display_name="Project ID (UUID)", field_type=FieldType.UUID,
                    width=36, required=False, mapping_to_db="id", order=1),
                TemplateColumn(field_name="name", display_name="Project Name *", field_type=FieldType.TEXT,
                    width=30, required=True, mapping_to_db="name", order=2),
                TemplateColumn(field_name="projectType", display_name="Project Type *", field_type=FieldType.ENUM,
                    width=20, required=True,
                    validation=ColumnValidation(validation_type=ValidationType.LIST,
                        options=DropdownDataSources.get_project_types()),
                    mapping_to_db="projectType", order=3),
                TemplateColumn(field_name="language", display_name="Language", field_type=FieldType.TEXT,
                    width=20, required=False, mapping_to_db="languageId",
                    transform_function="lookup_language_id", order=4),
                TemplateColumn(field_name="country", display_name="Country", field_type=FieldType.TEXT,
                    width=20, required=False, mapping_to_db="countryId",
                    transform_function="lookup_country_id", order=5),
                TemplateColumn(field_name="stage", display_name="Stage", field_type=FieldType.ENUM,
                    width=15, required=False, default_value="PLANNING",
                    validation=ColumnValidation(validation_type=ValidationType.LIST,
                        options=DropdownDataSources.get_project_stages()),
                    mapping_to_db="stage", order=6),
            ],
            example_row={"id": "", "name": "John's Bible Translation", "projectType": "TEXT_TRANSLATION",
                        "language": "Hindi", "country": "India", "stage": "IN_PROGRESS"}
        )
    ]
    
    return ExcelTemplate(
        name="project_import", display_name="Project Import Template",
        purpose=TemplatePurpose.PROJECT_IMPORT,
        description="Import or update project information", version="1.0", sheets=sheets,
        instructions="Project Name must be unique. Language and Country names will be matched.",
        requires_approval=True
    )


def get_assignment_import_template() -> ExcelTemplate:
    """Template for assigning users to projects"""
    
    sheets = [
        TemplateSheet(
            sheet_name="Assignments", purpose=TemplatePurpose.ASSIGNMENT_IMPORT,
            description="Assign users to projects with specific work items",
            table_name="users_to_projects", primary_key_fields=["userId", "projectId"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="userId", display_name="User ID or Username *", field_type=FieldType.TEXT,
                    width=25, required=True, mapping_to_db="userId", transform_function="resolve_user_id", order=1),
                TemplateColumn(field_name="projectId", display_name="Project ID or Name *", field_type=FieldType.TEXT,
                    width=25, required=True, mapping_to_db="projectId", transform_function="resolve_project_id", order=2),
                TemplateColumn(field_name="role", display_name="Role *", field_type=FieldType.ENUM,
                    width=15, required=True,
                    validation=ColumnValidation(validation_type=ValidationType.LIST,
                        options=DropdownDataSources.get_user_roles()),
                    mapping_to_db="role", order=3),
                TemplateColumn(field_name="verses", display_name="Assigned Verses", field_type=FieldType.VERSES,
                    width=40, required=False, description="Comma-separated verse IDs",
                    example="101001001,101001002", mapping_to_db="verses", transform_function="validate_verse_ids", order=4),
                TemplateColumn(field_name="obsChapters", display_name="OBS Chapters", field_type=FieldType.OBS_CHAPTERS,
                    width=20, required=False, description="Comma-separated chapter numbers (1-50)",
                    example="1,2,3,4,5", mapping_to_db="obsChapters", transform_function="validate_obs_chapters", order=5),
                TemplateColumn(field_name="literatureGenres", display_name="Literature Genres", field_type=FieldType.LITERATURE_GENRES,
                    width=30, required=False, description="Comma-separated genre IDs",
                    example="GEN001,GEN002", mapping_to_db="literatureGenres", order=6),
            ],
            example_row={"userId": "john_doe", "projectId": "John's Bible Translation", "role": "MTT",
                        "verses": "101001001,101001002", "obsChapters": "", "literatureGenres": ""}
        )
    ]
    
    return ExcelTemplate(
        name="assignment_import", display_name="Assignment Import Template",
        purpose=TemplatePurpose.ASSIGNMENT_IMPORT,
        description="Assign users to translation projects", version="1.0", sheets=sheets,
        instructions="For Bible projects, provide verse IDs. For OBS, provide chapter numbers.",
        requires_approval=True
    )


def get_worklog_import_template() -> ExcelTemplate:
    """Template for importing worklogs"""
    
    sheets = [
        TemplateSheet(
            sheet_name="Worklogs", purpose=TemplatePurpose.WORKLOG_IMPORT,
            description="Record translation work sessions", table_name="worklogs",
            primary_key_fields=["id"], update_mode="insert", batch_size=500,
            columns=[
                TemplateColumn(field_name="userId", display_name="User ID or Username *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_user_id", order=1),
                TemplateColumn(field_name="projectId", display_name="Project ID or Name *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_project_id", order=2),
                TemplateColumn(field_name="role", display_name="Role *", field_type=FieldType.ENUM, width=15, required=True,
                    validation=ColumnValidation(validation_type=ValidationType.LIST, options=DropdownDataSources.get_work_roles()), order=3),
                TemplateColumn(field_name="startDate", display_name="Start Date *", field_type=FieldType.DATE,
                    width=12, required=True, description="YYYY-MM-DD", example="2024-01-15", order=4),
                TemplateColumn(field_name="endDate", display_name="End Date *", field_type=FieldType.DATE,
                    width=12, required=True, description="YYYY-MM-DD", example="2024-01-15", order=5),
                TemplateColumn(field_name="translationSoftware", display_name="Software", field_type=FieldType.ENUM, width=15,
                    validation=ColumnValidation(validation_type=ValidationType.LIST,
                        options=DropdownDataSources.get_translation_software()), order=6),
                TemplateColumn(field_name="description", display_name="Description", field_type=FieldType.TEXT, width=40, order=7),
                TemplateColumn(field_name="noWork", display_name="No Work Done", field_type=FieldType.BOOLEAN, width=12,
                    default_value="false",
                    validation=ColumnValidation(validation_type=ValidationType.LIST, options=DropdownDataSources.get_boolean_options()), order=8),
                TemplateColumn(field_name="bookNo", display_name="Book Number", field_type=FieldType.INTEGER, width=10,
                    transform_function="map_book_number", group="Bible Translation", order=10),
                TemplateColumn(field_name="startChapter", display_name="Start Chapter", field_type=FieldType.INTEGER, width=12, group="Bible Translation", order=11),
                TemplateColumn(field_name="startVerse", display_name="Start Verse", field_type=FieldType.INTEGER, width=10, group="Bible Translation", order=12),
                TemplateColumn(field_name="endChapter", display_name="End Chapter", field_type=FieldType.INTEGER, width=12, group="Bible Translation", order=13),
                TemplateColumn(field_name="endVerse", display_name="End Verse", field_type=FieldType.INTEGER, width=10, group="Bible Translation", order=14),
                TemplateColumn(field_name="obsStartChapter", display_name="OBS Start Chapter", field_type=FieldType.INTEGER, width=15,
                    validation=ColumnValidation(validation_type=ValidationType.NUMBER_RANGE, min_value=1, max_value=50), group="OBS Translation", order=20),
                TemplateColumn(field_name="obsEndChapter", display_name="OBS End Chapter", field_type=FieldType.INTEGER, width=15,
                    validation=ColumnValidation(validation_type=ValidationType.NUMBER_RANGE, min_value=1, max_value=50), group="OBS Translation", order=21),
                TemplateColumn(field_name="obsStartPara", display_name="OBS Start Paragraph", field_type=FieldType.INTEGER, width=18, group="OBS Translation", order=22),
                TemplateColumn(field_name="obsEndPara", display_name="OBS End Paragraph", field_type=FieldType.INTEGER, width=18, group="OBS Translation", order=23),
                TemplateColumn(field_name="literatureGenre", display_name="Literature Genre", field_type=FieldType.TEXT, width=20, group="Literature Translation", order=30),
            ],
            example_row={"userId": "john_doe", "projectId": "John's Bible Translation", "role": "MTT",
                        "startDate": "2024-01-15", "endDate": "2024-01-15", "translationSoftware": "AUTOGRAPHA",
                        "description": "Translated Genesis chapter 1", "noWork": "false",
                        "bookNo": "101", "startChapter": "1", "startVerse": "1", "endChapter": "1", "endVerse": "31"}
        )
    ]
    
    return ExcelTemplate(
        name="worklog_import", display_name="Worklog Import Template",
        purpose=TemplatePurpose.WORKLOG_IMPORT,
        description="Record translation work sessions", version="1.0", sheets=sheets,
        instructions="Date format: YYYY-MM-DD. Set noWork=true if no translation was done.",
        requires_approval=False
    )


def get_bible_chapter_import_template() -> ExcelTemplate:
    """Template for importing Bible chapter translations"""
    
    sheets = [
        TemplateSheet(
            sheet_name="Bible_Chapters", purpose=TemplatePurpose.BIBLE_CHAPTER_IMPORT,
            description="Import Bible chapter translations", table_name="text_translation_chapters",
            primary_key_fields=["textTranslationBookId", "chapterNo"], update_mode="upsert", batch_size=50,
            columns=[
                TemplateColumn(field_name="projectName", display_name="Project Name *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_bible_project_id", order=1),
                TemplateColumn(field_name="bookNo", display_name="Book Number *", field_type=FieldType.INTEGER,
                    width=10, required=True, transform_function="map_book_number", order=2),
                TemplateColumn(field_name="chapterNo", display_name="Chapter Number *", field_type=FieldType.INTEGER,
                    width=10, required=True, order=3),
                TemplateColumn(field_name="verseNumber", display_name="Verse Number", field_type=FieldType.INTEGER,
                    width=10, required=False, order=4),
                TemplateColumn(field_name="translationText", display_name="Translation Text *", field_type=FieldType.TEXT,
                    width=80, required=True, transform_function="format_bible_content", order=5),
                TemplateColumn(field_name="version", display_name="Version", field_type=FieldType.INTEGER,
                    width=10, required=False, default_value="1", order=6),
            ],
            example_row={"projectName": "John's Bible Translation", "bookNo": "101", "chapterNo": "1",
                        "verseNumber": "1", "translationText": "In the beginning God created...", "version": "1"}
        )
    ]
    
    return ExcelTemplate(
        name="bible_chapter_import", display_name="Bible Chapter Import Template",
        purpose=TemplatePurpose.BIBLE_CHAPTER_IMPORT,
        description="Import Bible chapter translations", version="1.0", sheets=sheets,
        instructions="OT books: 101-166, NT books: 240-266. Increment version for updates.",
        requires_approval=True
    )


def get_obs_chapter_import_template() -> ExcelTemplate:
    """Template for importing OBS chapter translations"""
    
    sheets = [
        TemplateSheet(
            sheet_name="OBS_Chapters", purpose=TemplatePurpose.OBS_CHAPTER_IMPORT,
            description="Import OBS chapter translations", table_name="obs_project_chapters",
            primary_key_fields=["obsProjectId", "chapterNo"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="projectName", display_name="Project Name *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_obs_project_id", order=1),
                TemplateColumn(field_name="chapterNo", display_name="Chapter Number *", field_type=FieldType.INTEGER,
                    width=10, required=True, validation=ColumnValidation(validation_type=ValidationType.NUMBER_RANGE, min_value=1, max_value=50), order=2),
                TemplateColumn(field_name="title", display_name="Chapter Title *", field_type=FieldType.TEXT,
                    width=40, required=True, transform_function="format_obs_title", order=3),
                TemplateColumn(field_name="paragraphs", display_name="Paragraphs (JSON)", field_type=FieldType.JSON,
                    width=80, required=False, example='[{"content": "Paragraph 1"}]', transform_function="format_obs_paragraphs", order=4),
                TemplateColumn(field_name="bibleRef", display_name="Bible Reference", field_type=FieldType.TEXT,
                    width=30, required=False, transform_function="format_obs_bibleref", order=5),
                TemplateColumn(field_name="version", display_name="Version", field_type=FieldType.INTEGER,
                    width=10, required=False, default_value="1", order=6),
            ],
            example_row={"projectName": "John's OBS Project", "chapterNo": "1", "title": "The Creation",
                        "paragraphs": '[{"content": "God created the heavens and the earth."}]', "bibleRef": "Genesis 1:1", "version": "1"}
        ),
        TemplateSheet(
            sheet_name="OBS_Audio", purpose=TemplatePurpose.OBS_CHAPTER_IMPORT,
            description="Import OBS audio recordings", table_name="obs_audio_recordings",
            primary_key_fields=["obsProjectChapterId", "type", "paraIndex"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="projectName", display_name="Project Name *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_obs_project_id", order=1),
                TemplateColumn(field_name="chapterNo", display_name="Chapter Number *", field_type=FieldType.INTEGER, width=10, required=True, order=2),
                TemplateColumn(field_name="audioType", display_name="Audio Type *", field_type=FieldType.ENUM, width=10, required=True,
                    validation=ColumnValidation(validation_type=ValidationType.LIST,
                        options=[DropdownOption("title", "Title Audio"), DropdownOption("para", "Paragraph Audio")]), order=3),
                TemplateColumn(field_name="paraIndex", display_name="Paragraph Index", field_type=FieldType.INTEGER, width=12, order=4),
                TemplateColumn(field_name="recordingId", display_name="Recording URL/ID *", field_type=FieldType.TEXT, width=50, required=True, order=5),
            ]
        )
    ]
    
    return ExcelTemplate(
        name="obs_chapter_import", display_name="OBS Chapter Import Template",
        purpose=TemplatePurpose.OBS_CHAPTER_IMPORT,
        description="Import OBS chapter translations and audio recordings", version="1.0", sheets=sheets,
        instructions="For title audio, leave paraIndex empty. Paragraphs must be valid JSON.",
        requires_approval=True
    )


def get_literature_genre_import_template() -> ExcelTemplate:
    """Template for importing literature genre translations"""
    
    sheets = [
        TemplateSheet(
            sheet_name="Literature_Genres", purpose=TemplatePurpose.LITERATURE_GENRE_IMPORT,
            description="Import literature genre translations", table_name="literature_project_genres",
            primary_key_fields=["literatureProjectId", "genreId"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="projectName", display_name="Project Name *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_literature_project_id", order=1),
                TemplateColumn(field_name="genreId", display_name="Genre ID *", field_type=FieldType.TEXT, width=15, required=True,
                    validation=ColumnValidation(validation_type=ValidationType.LIST, options=DropdownDataSources.get_literature_genres()), order=2),
                TemplateColumn(field_name="genreName", display_name="Genre Name", field_type=FieldType.TEXT, width=25, order=3),
                TemplateColumn(field_name="content", display_name="Content (JSON)", field_type=FieldType.JSON,
                    width=80, required=True, transform_function="validate_literature_content",
                    example='{"content": [{"title": "Section 1", "content": "Text here"}]}', order=4),
                TemplateColumn(field_name="version", display_name="Version", field_type=FieldType.INTEGER, width=10, default_value="1", order=5),
            ],
            example_row={"projectName": "John's Literature Project", "genreId": "GEN001", "genreName": "Bible Story",
                        "content": '{"content": [{"title": "The Creation", "content": "In the beginning..."}]}', "version": "1"}
        )
    ]
    
    return ExcelTemplate(
        name="literature_genre_import", display_name="Literature Genre Import Template",
        purpose=TemplatePurpose.LITERATURE_GENRE_IMPORT,
        description="Import literature genre translations", version="1.0", sheets=sheets,
        instructions="Content must be valid JSON with a 'content' array.",
        requires_approval=True
    )


def get_grammar_import_template() -> ExcelTemplate:
    """Template for importing grammar translations"""
    
    sheets = []
    grammar_types = ["phrases", "pronouns", "connectives"]
    
    for grammar_type in grammar_types:
        sheets.append(TemplateSheet(
            sheet_name=f"Grammar_{grammar_type.capitalize()}", purpose=TemplatePurpose.GRAMMAR_IMPORT,
            description=f"Import {grammar_type} translations",
            table_name=f"grammar_{grammar_type}_project_contents",
            primary_key_fields=["grammarPhrasesProjectId"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="projectName", display_name="Project Name *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function=f"resolve_grammar_{grammar_type}_project_id", order=1),
                TemplateColumn(field_name="items", display_name=f"{grammar_type.capitalize()} (JSON) *", field_type=FieldType.JSON,
                    width=60, required=True, description=f"JSON array of {grammar_type}",
                    example=f'[{{"{grammar_type[:-1]}": "example"}}]', transform_function=f"validate_grammar_{grammar_type}", order=2),
                TemplateColumn(field_name="version", display_name="Version", field_type=FieldType.INTEGER, width=10, default_value="1", order=3),
                TemplateColumn(field_name="userId", display_name="User ID", field_type=FieldType.TEXT, width=25, transform_function="resolve_user_id", order=4),
            ],
            example_row={"projectName": f"John's Grammar {grammar_type.capitalize()}", "items": f'[{{"{grammar_type[:-1]}": "example"}}]', "version": "1", "userId": "john_doe"}
        ))
    
    return ExcelTemplate(
        name="grammar_import", display_name="Grammar Import Template",
        purpose=TemplatePurpose.GRAMMAR_IMPORT,
        description="Import grammar translations (phrases, pronouns, connectives)",
        version="1.0", sheets=sheets,
        instructions="Items must be valid JSON array with appropriate keys.",
        requires_approval=True
    )


# ============================================================
# Telios_LMS Template Definitions
# ============================================================

def get_batch_creation_template() -> ExcelTemplate:
    """Template for creating/updating batches"""
    
    sheets = [
        TemplateSheet(
            sheet_name="Batches", purpose=TemplatePurpose.BATCH_CREATION,
            description="Create or update training batches", table_name="batch",
            primary_key_fields=["id", "batch"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="id", display_name="Batch ID (UUID)", field_type=FieldType.UUID,
                    width=36, required=False, mapping_to_db="id", order=1),
                TemplateColumn(field_name="batch", display_name="Batch Name *", field_type=FieldType.TEXT,
                    width=25, required=True, description="Unique batch identifier",
                    example="BATCH_2024_001", mapping_to_db="batch", order=2),
                TemplateColumn(field_name="location", display_name="Location *", field_type=FieldType.TEXT,
                    width=30, required=True, description="Training location",
                    example="Bangalore, India", mapping_to_db="location", order=3),
                TemplateColumn(field_name="course", display_name="Course Name/ID *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_course_id", order=4),
                TemplateColumn(field_name="country", display_name="Country", field_type=FieldType.TEXT,
                    width=20, required=False, transform_function="lookup_lms_country_id", order=5),
                TemplateColumn(field_name="startDate", display_name="Start Date *", field_type=FieldType.DATE,
                    width=12, required=True, description="YYYY-MM-DD", example="2024-01-15", order=6),
                TemplateColumn(field_name="endDate", display_name="End Date *", field_type=FieldType.DATE,
                    width=12, required=True, description="YYYY-MM-DD", example="2024-03-15", order=7),
                TemplateColumn(field_name="batchstatus", display_name="Batch Status", field_type=FieldType.ENUM,
                    width=15, required=False, default_value="PLANNING",
                    validation=ColumnValidation(validation_type=ValidationType.LIST,
                        options=DropdownDataSources.get_batch_status_options()),
                    transform_function="resolve_batch_status_id", order=8),
                TemplateColumn(field_name="description", display_name="Description", field_type=FieldType.TEXT,
                    width=50, required=False, order=9),
            ],
            example_row={"id": "", "batch": "BATCH_2024_001", "location": "Bangalore, India",
                        "course": "Bible Translation Principles", "country": "India",
                        "startDate": "2024-01-15", "endDate": "2024-03-15", "batchstatus": "PLANNING",
                        "description": "First batch of 2024 for MTT training"}
        ),
        TemplateSheet(
            sheet_name="Courses", purpose=TemplatePurpose.BATCH_CREATION,
            description="Course definitions", table_name="course",
            primary_key_fields=["id", "title"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="id", display_name="Course ID (UUID)", field_type=FieldType.UUID,
                    width=36, required=False, mapping_to_db="id", order=1),
                TemplateColumn(field_name="title", display_name="Course Title *", field_type=FieldType.TEXT,
                    width=40, required=True, mapping_to_db="title", order=2),
                TemplateColumn(field_name="description", display_name="Course Description", field_type=FieldType.TEXT,
                    width=50, required=False, mapping_to_db="description", order=3),
                TemplateColumn(field_name="duration_weeks", display_name="Duration (Weeks)", field_type=FieldType.INTEGER,
                    width=15, required=False, order=4),
            ],
            example_row={"id": "", "title": "Bible Translation Principles", "description": "Foundational principles", "duration_weeks": "12"}
        )
    ]
    
    return ExcelTemplate(
        name="batch_creation", display_name="Batch Creation Template",
        purpose=TemplatePurpose.BATCH_CREATION,
        description="Create and manage training batches for LMS",
        version="1.0", sheets=sheets,
        instructions="Batch Name must be unique. Course can be existing or new.",
        requires_approval=True
    )


def get_student_enrollment_template() -> ExcelTemplate:
    """Template for enrolling students into batches"""
    
    sheets = [
        TemplateSheet(
            sheet_name="Enrollments", purpose=TemplatePurpose.STUDENT_ENROLLMENT,
            description="Enroll students into training batches", table_name="enrollment",
            primary_key_fields=["batch", "participant"], update_mode="upsert", batch_size=200,
            columns=[
                TemplateColumn(field_name="batch", display_name="Batch Name/ID *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_batch_id", order=1),
                TemplateColumn(field_name="participant", display_name="Participant ID/Email *", field_type=FieldType.TEXT,
                    width=30, required=True, transform_function="resolve_participant_id", order=2),
                TemplateColumn(field_name="role", display_name="Role *", field_type=FieldType.ENUM, width=15, required=True,
                    validation=ColumnValidation(validation_type=ValidationType.LIST, options=DropdownDataSources.get_lms_roles()), order=3),
                TemplateColumn(field_name="enrollmentDate", display_name="Enrollment Date", field_type=FieldType.DATE,
                    width=12, required=False, default_value="today", order=4),
                TemplateColumn(field_name="completionStatus", display_name="Completion Status", field_type=FieldType.ENUM, width=15,
                    default_value="ENROLLED",
                    validation=ColumnValidation(validation_type=ValidationType.LIST, options=DropdownDataSources.get_completion_status()), order=5),
                TemplateColumn(field_name="completionDate", display_name="Completion Date", field_type=FieldType.DATE, width=12, order=6),
                TemplateColumn(field_name="notes", display_name="Notes", field_type=FieldType.TEXT, width=40, order=7),
            ],
            example_row={"batch": "BATCH_2024_001", "participant": "john_doe@example.com", "role": "MTT",
                        "enrollmentDate": "2024-01-10", "completionStatus": "ENROLLED", "notes": ""}
        ),
        TemplateSheet(
            sheet_name="Participants", purpose=TemplatePurpose.STUDENT_ENROLLMENT,
            description="New participant information", table_name="person",
            primary_key_fields=["email"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="email", display_name="Email *", field_type=FieldType.EMAIL, width=30, required=True, order=1),
                TemplateColumn(field_name="firstName", display_name="First Name *", field_type=FieldType.TEXT, width=15, required=True, order=2),
                TemplateColumn(field_name="lastName", display_name="Last Name *", field_type=FieldType.TEXT, width=15, required=True, order=3),
                TemplateColumn(field_name="phone", display_name="Phone", field_type=FieldType.PHONE, width=15, order=4),
                TemplateColumn(field_name="gender", display_name="Gender", field_type=FieldType.ENUM, width=10,
                    validation=ColumnValidation(validation_type=ValidationType.LIST, options=DropdownDataSources.get_gender_options()), order=5),
                TemplateColumn(field_name="country", display_name="Country", field_type=FieldType.TEXT, width=20,
                    transform_function="lookup_lms_country_id", order=6),
                TemplateColumn(field_name="username", display_name="Username", field_type=FieldType.TEXT, width=20,
                    transform_function="generate_username_if_empty", order=7),
            ],
            example_row={"email": "new_student@example.com", "firstName": "John", "lastName": "Doe",
                        "phone": "+1234567890", "gender": "MALE", "country": "India", "username": ""}
        )
    ]
    
    return ExcelTemplate(
        name="student_enrollment", display_name="Student Enrollment Template",
        purpose=TemplatePurpose.STUDENT_ENROLLMENT,
        description="Enroll students into training batches",
        version="1.0", sheets=sheets,
        instructions="Batch must exist. Participant can be email, username, or ID.",
        requires_approval=True
    )


def get_batch_module_template() -> ExcelTemplate:
    """Template for assigning modules to batches"""
    
    sheets = [
        TemplateSheet(
            sheet_name="BatchModules", purpose=TemplatePurpose.BATCH_MODULE,
            description="Assign modules to batches", table_name="batchmodule",
            primary_key_fields=["batchid", "moduleid"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="batch", display_name="Batch Name/ID *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_batch_id", order=1),
                TemplateColumn(field_name="module", display_name="Module Name/ID *", field_type=FieldType.TEXT,
                    width=30, required=True, transform_function="resolve_module_id", order=2),
                TemplateColumn(field_name="order", display_name="Display Order", field_type=FieldType.INTEGER,
                    width=10, default_value="0", order=3),
                TemplateColumn(field_name="startDate", display_name="Start Date", field_type=FieldType.DATE, width=12, order=4),
                TemplateColumn(field_name="endDate", display_name="End Date", field_type=FieldType.DATE, width=12, order=5),
            ],
            example_row={"batch": "BATCH_2024_001", "module": "Introduction to Translation", "order": "1",
                        "startDate": "2024-01-15", "endDate": "2024-01-22"}
        ),
        TemplateSheet(
            sheet_name="Modules", purpose=TemplatePurpose.BATCH_MODULE,
            description="Module definitions", table_name="module",
            primary_key_fields=["id", "module"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="id", display_name="Module ID (UUID)", field_type=FieldType.UUID, width=36, required=False, order=1),
                TemplateColumn(field_name="module", display_name="Module Name *", field_type=FieldType.TEXT, width=30, required=True, order=2),
                TemplateColumn(field_name="description", display_name="Description", field_type=FieldType.TEXT, width=50, order=3),
                TemplateColumn(field_name="duration_hours", display_name="Duration (Hours)", field_type=FieldType.INTEGER, width=15, order=4),
            ],
            example_row={"id": "", "module": "Introduction to Translation", "description": "Basic concepts", "duration_hours": "10"}
        )
    ]
    
    return ExcelTemplate(
        name="batch_module", display_name="Batch Module Assignment Template",
        purpose=TemplatePurpose.BATCH_MODULE,
        description="Assign modules to training batches",
        version="1.0", sheets=sheets,
        instructions="Order determines module sequence. Dates are optional.",
        requires_approval=False
    )


def get_attendance_template() -> ExcelTemplate:
    """Template for recording attendance"""
    
    sheets = [
        TemplateSheet(
            sheet_name="Attendance", purpose=TemplatePurpose.ATTENDANCE,
            description="Record student attendance", table_name="attendance",
            primary_key_fields=["enrollment", "module", "date"], update_mode="upsert", batch_size=500,
            columns=[
                TemplateColumn(field_name="batch", display_name="Batch Name/ID *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_batch_id", order=1),
                TemplateColumn(field_name="participant", display_name="Participant Email/ID *", field_type=FieldType.TEXT,
                    width=30, required=True, transform_function="resolve_participant_id", order=2),
                TemplateColumn(field_name="module", display_name="Module Name/ID *", field_type=FieldType.TEXT,
                    width=30, required=True, transform_function="resolve_module_id", order=3),
                TemplateColumn(field_name="date", display_name="Date *", field_type=FieldType.DATE,
                    width=12, required=True, example="2024-01-15", order=4),
                TemplateColumn(field_name="status", display_name="Status *", field_type=FieldType.ENUM, width=12, required=True,
                    validation=ColumnValidation(validation_type=ValidationType.LIST, options=DropdownDataSources.get_attendance_status()), order=5),
                TemplateColumn(field_name="remarks", display_name="Remarks", field_type=FieldType.TEXT, width=40, order=6),
            ],
            example_row={"batch": "BATCH_2024_001", "participant": "john_doe@example.com",
                        "module": "Introduction to Translation", "date": "2024-01-15", "status": "PRESENT", "remarks": ""}
        )
    ]
    
    return ExcelTemplate(
        name="attendance", display_name="Attendance Recording Template",
        purpose=TemplatePurpose.ATTENDANCE,
        description="Record student attendance for modules",
        version="1.0", sheets=sheets,
        instructions="Status must be: PRESENT, ABSENT, LATE, EXCUSED, HALF_DAY",
        requires_approval=False
    )


def get_assignment_submission_template() -> ExcelTemplate:
    """Template for recording assignment submissions"""
    
    sheets = [
        TemplateSheet(
            sheet_name="Submissions", purpose=TemplatePurpose.ASSIGNMENT_SUBMISSION,
            description="Record assignment submissions", table_name="assignmentsubmission",
            primary_key_fields=["enrollment", "assignment"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="batch", display_name="Batch Name/ID *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_batch_id", order=1),
                TemplateColumn(field_name="participant", display_name="Participant Email/ID *", field_type=FieldType.TEXT,
                    width=30, required=True, transform_function="resolve_participant_id", order=2),
                TemplateColumn(field_name="assignment", display_name="Assignment Name/ID *", field_type=FieldType.TEXT,
                    width=30, required=True, transform_function="resolve_assignment_id", order=3),
                TemplateColumn(field_name="submissionDate", display_name="Submission Date *", field_type=FieldType.DATE,
                    width=12, required=True, order=4),
                TemplateColumn(field_name="submissionStatus", display_name="Status *", field_type=FieldType.ENUM, width=15, required=True,
                    validation=ColumnValidation(validation_type=ValidationType.LIST, options=DropdownDataSources.get_submission_status()), order=5),
                TemplateColumn(field_name="submissionUrl", display_name="Submission URL", field_type=FieldType.TEXT, width=50, order=6),
                TemplateColumn(field_name="feedback", display_name="Feedback", field_type=FieldType.TEXT, width=50, order=7),
                TemplateColumn(field_name="score", display_name="Score", field_type=FieldType.DECIMAL, width=10, order=8),
            ],
            example_row={"batch": "BATCH_2024_001", "participant": "john_doe@example.com",
                        "assignment": "Week 1 Assignment", "submissionDate": "2024-01-20",
                        "submissionStatus": "1", "submissionUrl": "https://drive.google.com/file/...", "score": ""}
        ),
        TemplateSheet(
            sheet_name="Assignments", purpose=TemplatePurpose.ASSIGNMENT_SUBMISSION,
            description="Assignment definitions", table_name="assignment",
            primary_key_fields=["id", "assignment"], update_mode="upsert",
            columns=[
                TemplateColumn(field_name="id", display_name="Assignment ID (UUID)", field_type=FieldType.UUID, width=36, required=False, order=1),
                TemplateColumn(field_name="assignment", display_name="Assignment Name *", field_type=FieldType.TEXT, width=30, required=True, order=2),
                TemplateColumn(field_name="assignmentkey", display_name="Assignment Key", field_type=FieldType.TEXT, width=20, order=3),
                TemplateColumn(field_name="description", display_name="Description", field_type=FieldType.TEXT, width=50, order=4),
                TemplateColumn(field_name="dueDate", display_name="Due Date", field_type=FieldType.DATE, width=12, order=5),
                TemplateColumn(field_name="maxScore", display_name="Max Score", field_type=FieldType.INTEGER, width=10, default_value="100", order=6),
            ],
            example_row={"id": "", "assignment": "Week 1 Assignment", "assignmentkey": "W1_ASSIGN",
                        "description": "Translation exercise", "dueDate": "2024-01-20", "maxScore": "100"}
        )
    ]
    
    return ExcelTemplate(
        name="assignment_submission", display_name="Assignment Submission Template",
        purpose=TemplatePurpose.ASSIGNMENT_SUBMISSION,
        description="Record assignment submissions and grades",
        version="1.0", sheets=sheets,
        instructions="Submission Status: 1=Submitted, 2=Redo, 3=Approved, 4=Rejected",
        requires_approval=True
    )


def get_survey_response_template() -> ExcelTemplate:
    """Template for importing survey responses"""
    
    sheets = [
        TemplateSheet(
            sheet_name="SurveyResponses", purpose=TemplatePurpose.SURVEY_RESPONSE,
            description="Import survey responses", table_name="response",
            primary_key_fields=["survey", "participant", "question"], update_mode="insert", batch_size=500,
            columns=[
                TemplateColumn(field_name="survey", display_name="Survey Name/ID *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_survey_id", order=1),
                TemplateColumn(field_name="participant", display_name="Participant Email/ID *", field_type=FieldType.TEXT,
                    width=30, required=True, transform_function="resolve_participant_id", order=2),
                TemplateColumn(field_name="batch", display_name="Batch Name/ID *", field_type=FieldType.TEXT,
                    width=25, required=True, transform_function="resolve_batch_id", order=3),
                TemplateColumn(field_name="question", display_name="Question *", field_type=FieldType.TEXT,
                    width=50, required=True, order=4),
                TemplateColumn(field_name="response", display_name="Response *", field_type=FieldType.TEXT,
                    width=50, required=True, order=5),
                TemplateColumn(field_name="role", display_name="Role", field_type=FieldType.ENUM, width=15,
                    validation=ColumnValidation(validation_type=ValidationType.LIST, options=DropdownDataSources.get_lms_roles()), order=6),
                TemplateColumn(field_name="responseDate", display_name="Response Date", field_type=FieldType.DATE,
                    width=12, default_value="today", order=7),
            ],
            example_row={"survey": "End of Course Survey", "participant": "john_doe@example.com",
                        "batch": "BATCH_2024_001", "question": "How would you rate the course?",
                        "response": "Excellent", "role": "MTT", "responseDate": "2024-03-20"}
        )
    ]
    
    return ExcelTemplate(
        name="survey_response", display_name="Survey Response Template",
        purpose=TemplatePurpose.SURVEY_RESPONSE,
        description="Import survey responses from participants",
        version="1.0", sheets=sheets,
        instructions="Each row is one response to one question.",
        requires_approval=False
    )


# ============================================================
# Template Manager
# ============================================================

class ExcelTemplateManager:
    """Manager for Excel templates"""
    
    def __init__(self, template_dir: str = "./output/templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[TemplatePurpose, ExcelTemplate] = {}
        self._load_all_templates()
    
    def _load_all_templates(self):
        """Load all template definitions"""
        # AG_Dev Templates
        self.templates[TemplatePurpose.USER_IMPORT] = get_user_import_template()
        self.templates[TemplatePurpose.PROJECT_IMPORT] = get_project_import_template()
        self.templates[TemplatePurpose.ASSIGNMENT_IMPORT] = get_assignment_import_template()
        self.templates[TemplatePurpose.WORKLOG_IMPORT] = get_worklog_import_template()
        self.templates[TemplatePurpose.BIBLE_CHAPTER_IMPORT] = get_bible_chapter_import_template()
        self.templates[TemplatePurpose.OBS_CHAPTER_IMPORT] = get_obs_chapter_import_template()
        self.templates[TemplatePurpose.LITERATURE_GENRE_IMPORT] = get_literature_genre_import_template()
        self.templates[TemplatePurpose.GRAMMAR_IMPORT] = get_grammar_import_template()
        
        # Telios_LMS Templates
        self.templates[TemplatePurpose.BATCH_CREATION] = get_batch_creation_template()
        self.templates[TemplatePurpose.STUDENT_ENROLLMENT] = get_student_enrollment_template()
        self.templates[TemplatePurpose.BATCH_MODULE] = get_batch_module_template()
        self.templates[TemplatePurpose.ATTENDANCE] = get_attendance_template()
        self.templates[TemplatePurpose.ASSIGNMENT_SUBMISSION] = get_assignment_submission_template()
        self.templates[TemplatePurpose.SURVEY_RESPONSE] = get_survey_response_template()
    
    def get_template(self, purpose: TemplatePurpose) -> Optional[ExcelTemplate]:
        """Get a template by purpose"""
        return self.templates.get(purpose)
    
    def get_template_by_name(self, name: str) -> Optional[ExcelTemplate]:
        """Get a template by name"""
        for template in self.templates.values():
            if template.name == name:
                return template
        return None
    
    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates"""
        return [
            {
                "name": t.name,
                "display_name": t.display_name,
                "purpose": t.purpose.value,
                "description": t.description,
                "sheets": len(t.sheets),
                "requires_approval": t.requires_approval
            }
            for t in self.templates.values()
        ]
    
    def get_template_path(self, purpose: TemplatePurpose) -> Path:
        """Get the file path for a template"""
        template = self.get_template(purpose)
        if not template:
            return None
        return self.template_dir / f"{template.name}.xlsx"
    
    def template_exists(self, purpose: TemplatePurpose) -> bool:
        """Check if a template file exists"""
        path = self.get_template_path(purpose)
        return path.exists() if path else False


# Singleton instance
_excel_template_manager = None

def get_excel_template_manager() -> ExcelTemplateManager:
    """Get the singleton instance"""
    global _excel_template_manager
    if _excel_template_manager is None:
        _excel_template_manager = ExcelTemplateManager()
    return _excel_template_manager