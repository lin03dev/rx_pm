"""
Field Mapping Configuration - Dynamic field mappings for tables
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class FieldMapping:
    """Mapping for a field across different contexts"""
    source_table: str
    source_field: str
    target_table: Optional[str] = None
    target_field: Optional[str] = None
    field_type: str = "string"  # string, integer, json, date, uuid
    is_required: bool = False
    is_foreign_key: bool = False
    foreign_key_ref: Optional[str] = None
    transform_function: Optional[str] = None  # e.g., "map_book", "parse_json"
    description: str = ""


@dataclass
class TableFieldMapping:
    """Complete field mapping for a table"""
    table_name: str
    display_name: str
    fields: Dict[str, FieldMapping] = field(default_factory=dict)
    
    # Common query patterns
    common_selects: List[str] = field(default_factory=list)
    common_joins: List[str] = field(default_factory=list)
    common_where: List[str] = field(default_factory=list)


class FieldMappingConfig:
    """Dynamic configuration for field mappings across all tables"""
    
    def __init__(self, config_file: str = None):
        self.table_mappings: Dict[str, TableFieldMapping] = {}
        self._load_default_mappings()
        if config_file:
            self._load_from_file(config_file)
    
    def _load_default_mappings(self):
        """Load default field mappings for all important tables"""
        
        # ============================================================
        # Users and Person Tables
        # ============================================================
        users_mapping = TableFieldMapping(
            table_name="users",
            display_name="Users",
            fields={
                "id": FieldMapping("users", "id", field_type="uuid", is_required=True),
                "username": FieldMapping("users", "username", field_type="string"),
                "email": FieldMapping("users", "email", field_type="string"),
                "role": FieldMapping("users", "role", field_type="enum"),
                "name": FieldMapping("users", "name", field_type="string"),
                "personId": FieldMapping("users", "personId", field_type="uuid", 
                                       is_foreign_key=True, foreign_key_ref="person.id"),
                "createdAt": FieldMapping("users", "createdAt", field_type="datetime"),
                "updatedAt": FieldMapping("users", "updatedAt", field_type="datetime"),
                "isActive": FieldMapping("users", "isActive", field_type="boolean")
            },
            common_selects=[
                "u.id, u.username, u.email, u.role::text as user_role",
                "u.name as display_name, u.\"createdAt\""
            ],
            common_joins=[
                "LEFT JOIN person p ON u.\"personId\"::text = p.id",
                "LEFT JOIN countries c ON p.\"countryId\" = c.id"
            ]
        )
        self.table_mappings["users"] = users_mapping
        
        # Person table
        person_mapping = TableFieldMapping(
            table_name="person",
            display_name="Person",
            fields={
                "id": FieldMapping("person", "id", field_type="uuid"),
                "firstName": FieldMapping("person", "firstName", field_type="string"),
                "lastName": FieldMapping("person", "lastName", field_type="string"),
                "phone": FieldMapping("person", "phone", field_type="string"),
                "email": FieldMapping("person", "email", field_type="string"),
                "countryId": FieldMapping("person", "countryId", field_type="uuid",
                                        is_foreign_key=True, foreign_key_ref="countries.id"),
                "gender": FieldMapping("person", "gender", field_type="enum"),
                "state": FieldMapping("person", "state", field_type="string"),
                "city": FieldMapping("person", "city", field_type="string")
            }
        )
        self.table_mappings["person"] = person_mapping
        
        # Countries table
        countries_mapping = TableFieldMapping(
            table_name="countries",
            display_name="Countries",
            fields={
                "id": FieldMapping("countries", "id", field_type="uuid"),
                "name": FieldMapping("countries", "name", field_type="string"),
                "countryCode": FieldMapping("countries", "countryCode", field_type="string")
            }
        )
        self.table_mappings["countries"] = countries_mapping
        
        # ============================================================
        # Projects Tables
        # ============================================================
        projects_mapping = TableFieldMapping(
            table_name="projects",
            display_name="Projects",
            fields={
                "id": FieldMapping("projects", "id", field_type="uuid"),
                "name": FieldMapping("projects", "name", field_type="string"),
                "projectType": FieldMapping("projects", "projectType", field_type="enum"),
                "stage": FieldMapping("projects", "stage", field_type="enum"),
                "languageId": FieldMapping("projects", "languageId", field_type="uuid",
                                         is_foreign_key=True, foreign_key_ref="languages.id"),
                "countryId": FieldMapping("projects", "countryId", field_type="uuid",
                                        is_foreign_key=True, foreign_key_ref="countries.id"),
                "createdAt": FieldMapping("projects", "createdAt", field_type="datetime"),
                "updatedAt": FieldMapping("projects", "updatedAt", field_type="datetime")
            },
            common_selects=[
                "p.id, p.name, p.\"projectType\", p.stage",
                "l.name as language_name, c.name as country"
            ],
            common_joins=[
                "LEFT JOIN languages l ON p.\"languageId\" = l.id",
                "LEFT JOIN countries c ON p.\"countryId\" = c.id"
            ]
        )
        self.table_mappings["projects"] = projects_mapping
        
        # Languages table
        languages_mapping = TableFieldMapping(
            table_name="languages",
            display_name="Languages",
            fields={
                "id": FieldMapping("languages", "id", field_type="uuid"),
                "name": FieldMapping("languages", "name", field_type="string"),
                "isoCode": FieldMapping("languages", "isoCode", field_type="string"),
                "countryId": FieldMapping("languages", "countryId", field_type="uuid")
            }
        )
        self.table_mappings["languages"] = languages_mapping
        
        # ============================================================
        # Assignments Table
        # ============================================================
        assignments_mapping = TableFieldMapping(
            table_name="users_to_projects",
            display_name="User-Project Assignments",
            fields={
                "userId": FieldMapping("users_to_projects", "userId", field_type="uuid",
                                      is_foreign_key=True, foreign_key_ref="users.id"),
                "projectId": FieldMapping("users_to_projects", "projectId", field_type="uuid",
                                         is_foreign_key=True, foreign_key_ref="projects.id"),
                "role": FieldMapping("users_to_projects", "role", field_type="enum"),
                "verses": FieldMapping("users_to_projects", "verses", field_type="string",
                                     description="Comma-separated verse IDs for Bible projects"),
                "obsChapters": FieldMapping("users_to_projects", "obsChapters", field_type="string",
                                          description="Comma-separated chapter numbers for OBS"),
                "literatureGenres": FieldMapping("users_to_projects", "literatureGenres", field_type="string",
                                               description="Comma-separated genre IDs for Literature"),
                "assignments": FieldMapping("users_to_projects", "assignments", field_type="json",
                                          description="JSON field for complex assignments"),
                "createdAt": FieldMapping("users_to_projects", "createdAt", field_type="datetime"),
                "updatedAt": FieldMapping("users_to_projects", "updatedAt", field_type="datetime")
            },
            common_selects=[
                "utp.\"userId\", utp.\"projectId\", utp.role",
                "utp.verses, utp.\"obsChapters\", utp.\"literatureGenres\""
            ]
        )
        self.table_mappings["users_to_projects"] = assignments_mapping
        
        # ============================================================
        # Content Tables (Bible)
        # ============================================================
        text_translation_projects_mapping = TableFieldMapping(
            table_name="text_translation_projects",
            display_name="Bible Translation Projects",
            fields={
                "id": FieldMapping("text_translation_projects", "id", field_type="uuid"),
                "projectId": FieldMapping("text_translation_projects", "projectId", field_type="uuid",
                                         is_foreign_key=True, foreign_key_ref="projects.id")
            }
        )
        self.table_mappings["text_translation_projects"] = text_translation_projects_mapping
        
        text_translation_books_mapping = TableFieldMapping(
            table_name="text_translation_books",
            display_name="Bible Translation Books",
            fields={
                "id": FieldMapping("text_translation_books", "id", field_type="uuid"),
                "textTranslationProjectId": FieldMapping("text_translation_books", "textTranslationProjectId",
                                                        field_type="uuid", is_foreign_key=True),
                "bookNo": FieldMapping("text_translation_books", "bookNo", field_type="integer",
                                     transform_function="map_book")
            }
        )
        self.table_mappings["text_translation_books"] = text_translation_books_mapping
        
        text_translation_chapters_mapping = TableFieldMapping(
            table_name="text_translation_chapters",
            display_name="Bible Translation Chapters",
            fields={
                "id": FieldMapping("text_translation_chapters", "id", field_type="uuid"),
                "textTranslationBookId": FieldMapping("text_translation_chapters", "textTranslationBookId",
                                                     field_type="uuid", is_foreign_key=True),
                "chapterNo": FieldMapping("text_translation_chapters", "chapterNo", field_type="integer"),
                "content": FieldMapping("text_translation_chapters", "content", field_type="json",
                                      transform_function="parse_bible_content"),
                "version": FieldMapping("text_translation_chapters", "version", field_type="integer")
            },
            common_selects=[
                "ttc.\"chapterNo\", ttc.version, ttc.content::text as content_text"
            ]
        )
        self.table_mappings["text_translation_chapters"] = text_translation_chapters_mapping
        
        # ============================================================
        # Content Tables (OBS)
        # ============================================================
        obs_projects_mapping = TableFieldMapping(
            table_name="obs_projects",
            display_name="OBS Projects",
            fields={
                "id": FieldMapping("obs_projects", "id", field_type="uuid"),
                "projectId": FieldMapping("obs_projects", "projectId", field_type="uuid",
                                         is_foreign_key=True, foreign_key_ref="projects.id")
            }
        )
        self.table_mappings["obs_projects"] = obs_projects_mapping
        
        obs_chapters_mapping = TableFieldMapping(
            table_name="obs_project_chapters",
            display_name="OBS Chapters",
            fields={
                "id": FieldMapping("obs_project_chapters", "id", field_type="uuid"),
                "obsProjectId": FieldMapping("obs_project_chapters", "obsProjectId", field_type="uuid",
                                            is_foreign_key=True),
                "chapterNo": FieldMapping("obs_project_chapters", "chapterNo", field_type="integer"),
                "data": FieldMapping("obs_project_chapters", "data", field_type="json",
                                   transform_function="parse_obs_content"),
                "version": FieldMapping("obs_project_chapters", "version", field_type="integer")
            }
        )
        self.table_mappings["obs_project_chapters"] = obs_chapters_mapping
        
        # ============================================================
        # Content Tables (Literature)
        # ============================================================
        literature_projects_mapping = TableFieldMapping(
            table_name="literature_projects",
            display_name="Literature Projects",
            fields={
                "id": FieldMapping("literature_projects", "id", field_type="uuid"),
                "projectId": FieldMapping("literature_projects", "projectId", field_type="uuid",
                                         is_foreign_key=True, foreign_key_ref="projects.id")
            }
        )
        self.table_mappings["literature_projects"] = literature_projects_mapping
        
        literature_genres_mapping = TableFieldMapping(
            table_name="literature_project_genres",
            display_name="Literature Genres",
            fields={
                "id": FieldMapping("literature_project_genres", "id", field_type="uuid"),
                "literatureProjectId": FieldMapping("literature_project_genres", "literatureProjectId",
                                                   field_type="uuid", is_foreign_key=True),
                "genreId": FieldMapping("literature_project_genres", "genreId", field_type="string"),
                "content": FieldMapping("literature_project_genres", "content", field_type="json",
                                      transform_function="parse_literature_content"),
                "version": FieldMapping("literature_project_genres", "version", field_type="integer")
            }
        )
        self.table_mappings["literature_project_genres"] = literature_genres_mappings
        
        # ============================================================
        # Content Tables (Grammar)
        # ============================================================
        grammar_phrases_mapping = TableFieldMapping(
            table_name="grammar_phrases_project_contents",
            display_name="Grammar Phrases Content",
            fields={
                "id": FieldMapping("grammar_phrases_project_contents", "id", field_type="uuid"),
                "grammarPhrasesProjectId": FieldMapping("grammar_phrases_project_contents", 
                                                       "grammarPhrasesProjectId", field_type="uuid"),
                "content": FieldMapping("grammar_phrases_project_contents", "content", field_type="json",
                                      transform_function="parse_grammar_content"),
                "version": FieldMapping("grammar_phrases_project_contents", "version", field_type="integer"),
                "userId": FieldMapping("grammar_phrases_project_contents", "userId", field_type="uuid",
                                     is_foreign_key=True, foreign_key_ref="users.id")
            }
        )
        self.table_mappings["grammar_phrases_project_contents"] = grammar_phrases_mapping
        
        # Grammar history tables
        grammar_history_mapping = TableFieldMapping(
            table_name="grammar_phrases_project_content_history",
            display_name="Grammar Phrases History",
            fields={
                "grammarPhrasesProjectContentId": FieldMapping(
                    "grammar_phrases_project_content_history", "grammarPhrasesProjectContentId", 
                    field_type="uuid"),
                "version": FieldMapping("grammar_phrases_project_content_history", "version", 
                                       field_type="integer"),
                "content": FieldMapping("grammar_phrases_project_content_history", "content", 
                                      field_type="json"),
                "userId": FieldMapping("grammar_phrases_project_content_history", "userId", 
                                     field_type="uuid")
            }
        )
        self.table_mappings["grammar_phrases_project_content_history"] = grammar_history_mapping
        
        # Similar for pronouns and connectives (abbreviated for brevity)
        
        # ============================================================
        # Audio Tables (OBS)
        # ============================================================
        obs_audio_mapping = TableFieldMapping(
            table_name="obs_audio_recordings",
            display_name="OBS Audio Recordings",
            fields={
                "id": FieldMapping("obs_audio_recordings", "id", field_type="uuid"),
                "obsProjectChapterId": FieldMapping("obs_audio_recordings", "obsProjectChapterId", 
                                                   field_type="uuid", is_foreign_key=True),
                "type": FieldMapping("obs_audio_recordings", "type", field_type="enum",
                                   description="title or para"),
                "paraIndex": FieldMapping("obs_audio_recordings", "paraIndex", field_type="integer"),
                "recordingId": FieldMapping("obs_audio_recordings", "recordingId", field_type="string"),
                "version": FieldMapping("obs_audio_recordings", "version", field_type="integer")
            }
        )
        self.table_mappings["obs_audio_recordings"] = obs_audio_mapping
        
        # ============================================================
        # Worklogs Table
        # ============================================================
        worklogs_mapping = TableFieldMapping(
            table_name="worklogs",
            display_name="Worklogs",
            fields={
                "id": FieldMapping("worklogs", "id", field_type="uuid"),
                "projectId": FieldMapping("worklogs", "projectId", field_type="uuid",
                                         is_foreign_key=True, foreign_key_ref="projects.id"),
                "userId": FieldMapping("worklogs", "userId", field_type="uuid",
                                      is_foreign_key=True, foreign_key_ref="users.id"),
                "role": FieldMapping("worklogs", "role", field_type="enum"),
                "startDate": FieldMapping("worklogs", "startDate", field_type="datetime"),
                "endDate": FieldMapping("worklogs", "endDate", field_type="datetime"),
                "description": FieldMapping("worklogs", "description", field_type="string"),
                "translationSoftware": FieldMapping("worklogs", "translationSoftware", field_type="string"),
                "stage": FieldMapping("worklogs", "stage", field_type="enum"),
                "noWork": FieldMapping("worklogs", "noWork", field_type="boolean"),
                # Bible fields
                "bookNo": FieldMapping("worklogs", "bookNo", field_type="integer",
                                     transform_function="map_book"),
                "startChapter": FieldMapping("worklogs", "startChapter", field_type="integer"),
                "startVerse": FieldMapping("worklogs", "startVerse", field_type="integer"),
                "endChapter": FieldMapping("worklogs", "endChapter", field_type="integer"),
                "endVerse": FieldMapping("worklogs", "endVerse", field_type="integer"),
                # OBS fields
                "obsStartChapter": FieldMapping("worklogs", "obsStartChapter", field_type="integer"),
                "obsEndChapter": FieldMapping("worklogs", "obsEndChapter", field_type="integer"),
                "obsStartPara": FieldMapping("worklogs", "obsStartPara", field_type="integer"),
                "obsEndPara": FieldMapping("worklogs", "obsEndPara", field_type="integer"),
                # Literature fields
                "literatureGenre": FieldMapping("worklogs", "literatureGenre", field_type="string")
            },
            common_selects=[
                "w.id, w.\"projectId\", w.\"userId\", w.role",
                "w.\"startDate\", w.\"endDate\", w.description",
                "w.\"translationSoftware\", w.stage"
            ],
            common_joins=[
                "LEFT JOIN users u ON w.\"userId\" = u.id",
                "LEFT JOIN projects p ON w.\"projectId\" = p.id"
            ]
        )
        self.table_mappings["worklogs"] = worklogs_mapping
    
    def _load_from_file(self, config_file: str):
        """Load mappings from JSON file"""
        try:
            path = Path(config_file)
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                    # Override mappings from file
                    print(f"✅ Loaded field mappings from {config_file}")
        except Exception as e:
            print(f"⚠️ Could not load field mappings: {e}")
    
    def get_table_mapping(self, table_name: str) -> Optional[TableFieldMapping]:
        """Get field mapping for a table"""
        return self.table_mappings.get(table_name)
    
    def get_field_mapping(self, table_name: str, field_name: str) -> Optional[FieldMapping]:
        """Get mapping for a specific field"""
        table = self.table_mappings.get(table_name)
        if table:
            return table.fields.get(field_name)
        return None
    
    def get_transform_function(self, table_name: str, field_name: str) -> Optional[str]:
        """Get transform function for a field"""
        field = self.get_field_mapping(table_name, field_name)
        return field.transform_function if field else None
    
    def generate_select_clause(self, table_name: str, alias: str = None) -> str:
        """Generate a SELECT clause for a table based on mappings"""
        table = self.table_mappings.get(table_name)
        if not table:
            return f"SELECT * FROM {table_name}"
        
        if table.common_selects:
            return f"SELECT {', '.join(table.common_selects)}"
        
        fields = []
        prefix = f"{alias}." if alias else ""
        for field_name, mapping in table.fields.items():
            if mapping.is_required or mapping.field_type != "json":  # Skip heavy JSON fields by default
                fields.append(f'{prefix}"{field_name}"')
        
        return f"SELECT {', '.join(fields[:20])}"  # Limit to 20 fields
    
    def generate_join_clause(self, table_name: str, alias: str = None) -> List[str]:
        """Generate JOIN clauses for a table based on foreign key mappings"""
        table = self.table_mappings.get(table_name)
        if not table:
            return []
        
        if table.common_joins:
            return table.common_joins
        
        joins = []
        prefix = f"{alias}." if alias else ""
        for field_name, mapping in table.fields.items():
            if mapping.is_foreign_key and mapping.foreign_key_ref:
                ref_table, ref_field = mapping.foreign_key_ref.split('.')
                joins.append(f'LEFT JOIN {ref_table} ON {prefix}"{field_name}" = {ref_table}.{ref_field}')
        
        return joins


# Singleton instance
_field_mapping_config = None

def get_field_mapping_config(config_file: str = None) -> FieldMappingConfig:
    """Get the singleton instance"""
    global _field_mapping_config
    if _field_mapping_config is None:
        _field_mapping_config = FieldMappingConfig(config_file)
    return _field_mapping_config