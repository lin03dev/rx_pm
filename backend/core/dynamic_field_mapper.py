"""
Dynamic Field Mapper - Handle inconsistent column names across tables
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class FieldMappingStrategy(Enum):
    EXACT = "exact"
    CASE_INSENSITIVE = "case_insensitive"
    SCREAMING_SNAKE = "screaming_snake"  # UPPER_CASE
    CAMEL_CASE = "camel_case"  # camelCase
    SNAKE_CASE = "snake_case"  # snake_case
    PASCAL_CASE = "pascal_case"  # PascalCase


@dataclass
class TableFieldMap:
    """Mapping for a table's fields"""
    table_name: str
    field_aliases: Dict[str, List[str]] = field(default_factory=dict)
    strategy: FieldMappingStrategy = FieldMappingStrategy.CASE_INSENSITIVE
    
    def add_alias(self, canonical: str, *aliases: str):
        """Add aliases for a canonical field name"""
        if canonical not in self.field_aliases:
            self.field_aliases[canonical] = []
        self.field_aliases[canonical].extend(aliases)
    
    def get_canonical(self, field_name: str) -> Optional[str]:
        """Get canonical field name from alias"""
        # Check exact match
        if field_name in self.field_aliases:
            return field_name
        
        # Check aliases
        for canonical, aliases in self.field_aliases.items():
            if field_name in aliases:
                return canonical
        
        # Try case-insensitive
        field_lower = field_name.lower()
        for canonical, aliases in self.field_aliases.items():
            if canonical.lower() == field_lower:
                return canonical
            for alias in aliases:
                if alias.lower() == field_lower:
                    return canonical
        
        return None


class DynamicFieldMapper:
    """Dynamic mapper for inconsistent field names"""
    
    def __init__(self):
        self.table_maps: Dict[str, TableFieldMap] = {}
        self._load_default_mappings()
    
    def _load_default_mappings(self):
        """Load default field mappings"""
        
        # Projects table mappings
        projects_map = TableFieldMap("projects")
        projects_map.add_alias("id", "project_id", "projectId")
        projects_map.add_alias("name", "project_name", "projectName")
        projects_map.add_alias("projectType", "project_type", "projecttype", "type")
        projects_map.add_alias("stage", "project_stage", "projectStage")
        projects_map.add_alias("languageId", "language_id", "language")
        projects_map.add_alias("countryId", "country_id", "country")
        self.table_maps["projects"] = projects_map
        
        # Users table mappings
        users_map = TableFieldMap("users")
        users_map.add_alias("id", "user_id", "userId")
        users_map.add_alias("username", "user_name", "userName", "name")
        users_map.add_alias("email", "user_email", "userEmail")
        users_map.add_alias("role", "user_role", "userRole")
        users_map.add_alias("personId", "person_id", "personId")
        self.table_maps["users"] = users_map
        
        # Person table mappings
        person_map = TableFieldMap("person")
        person_map.add_alias("id", "person_id", "personId")
        person_map.add_alias("firstName", "first_name", "firstname")
        person_map.add_alias("lastName", "last_name", "lastname")
        person_map.add_alias("phone", "phone_number", "phoneNumber")
        self.table_maps["person"] = person_map
        
        # Users to projects mappings
        utp_map = TableFieldMap("users_to_projects")
        utp_map.add_alias("userId", "user_id", "user")
        utp_map.add_alias("projectId", "project_id", "project")
        utp_map.add_alias("role", "project_role", "projectRole")
        utp_map.add_alias("verses", "assigned_verses", "verses_assigned")
        utp_map.add_alias("obsChapters", "obs_chapters", "chapters")
        utp_map.add_alias("literatureGenres", "literature_genres", "genres")
        self.table_maps["users_to_projects"] = utp_map
        
        # Worklogs table mappings
        worklogs_map = TableFieldMap("worklogs")
        worklogs_map.add_alias("userId", "user_id", "user")
        worklogs_map.add_alias("projectId", "project_id", "project")
        worklogs_map.add_alias("startDate", "start_date", "start")
        worklogs_map.add_alias("endDate", "end_date", "end")
        worklogs_map.add_alias("noWork", "no_work", "nowork")
        worklogs_map.add_alias("bookNo", "book_no", "book")
        worklogs_map.add_alias("startChapter", "start_chapter", "chapter_start")
        worklogs_map.add_alias("startVerse", "start_verse", "verse_start")
        worklogs_map.add_alias("endChapter", "end_chapter", "chapter_end")
        worklogs_map.add_alias("endVerse", "end_verse", "verse_end")
        worklogs_map.add_alias("obsStartChapter", "obs_start_chapter")
        worklogs_map.add_alias("obsEndChapter", "obs_end_chapter")
        worklogs_map.add_alias("obsStartPara", "obs_start_para")
        worklogs_map.add_alias("obsEndPara", "obs_end_para")
        worklogs_map.add_alias("literatureGenre", "literature_genre", "genre")
        worklogs_map.add_alias("translationSoftware", "translation_software", "software")
        self.table_maps["worklogs"] = worklogs_map
        
        # Grammar tables (dynamic patterns)
        for grammar_type in ['phrases', 'pronouns', 'connectives']:
            table_name = f"grammar_{grammar_type}_projects"
            content_table = f"grammar_{grammar_type}_project_contents"
            history_table = f"grammar_{grammar_type}_project_content_history"
            
            grammar_map = TableFieldMap(table_name)
            grammar_map.add_alias("id", f"{grammar_type}_project_id")
            grammar_map.add_alias("projectId", "project_id", "project")
            self.table_maps[table_name] = grammar_map
            
            content_map = TableFieldMap(content_table)
            content_map.add_alias(f"grammar{grammar_type.capitalize()}ProjectId", 
                                 f"{grammar_type}_project_id", "project_id")
            content_map.add_alias("content", "data", "json_content")
            content_map.add_alias("version", "ver", "v")
            self.table_maps[content_table] = content_map
            
            history_map = TableFieldMap(history_table)
            history_map.add_alias(f"grammar{grammar_type.capitalize()}ProjectContentId", 
                                 f"{grammar_type}_content_id", "content_id")
            history_map.add_alias("version", "ver", "v")
            history_map.add_alias("userId", "user_id", "user")
            self.table_maps[history_table] = history_map
    
    def get_table_map(self, table_name: str) -> Optional[TableFieldMap]:
        """Get field map for a table"""
        return self.table_maps.get(table_name.lower())
    
    def map_field(self, table_name: str, field_name: str) -> Optional[str]:
        """Map a field to its canonical name"""
        table_map = self.get_table_map(table_name)
        if table_map:
            return table_map.get_canonical(field_name)
        return field_name
    
    def normalize_record(self, table_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a record to use canonical field names"""
        normalized = {}
        table_map = self.get_table_map(table_name)
        
        if not table_map:
            return record
        
        for key, value in record.items():
            canonical = table_map.get_canonical(key)
            if canonical:
                normalized[canonical] = value
            else:
                normalized[key] = value
        
        return normalized
    
    def add_custom_mapping(self, table_name: str, canonical: str, *aliases: str):
        """Add a custom mapping for a table"""
        table_name_lower = table_name.lower()
        if table_name_lower not in self.table_maps:
            self.table_maps[table_name_lower] = TableFieldMap(table_name)
        self.table_maps[table_name_lower].add_alias(canonical, *aliases)
    
    def discover_table_columns(self, db_manager, table_name: str, db_name: str = None) -> Dict[str, str]:
        """Discover actual columns in a table and suggest mappings"""
        try:
            query = f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            AND table_schema = 'public'
            ORDER BY ordinal_position
            """
            df = db_manager.execute_query(query, db_name=db_name)
            
            columns = {}
            for _, row in df.iterrows():
                columns[row['column_name']] = row['data_type']
            
            return columns
        except:
            return {}


# Singleton instance
_field_mapper = None

def get_field_mapper() -> DynamicFieldMapper:
    """Get singleton instance"""
    global _field_mapper
    if _field_mapper is None:
        _field_mapper = DynamicFieldMapper()
    return _field_mapper
