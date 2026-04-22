"""
Relationship Configuration - Dynamic table relationship definitions
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RelationshipType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


@dataclass
class Relationship:
    """Definition of a relationship between two tables"""
    name: str
    from_table: str
    to_table: str
    relationship_type: RelationshipType
    from_field: str
    to_field: str
    description: str = ""
    
    # For many-to-many, the junction table
    junction_table: Optional[str] = None
    junction_from_field: Optional[str] = None
    junction_to_field: Optional[str] = None


@dataclass
class RelationshipGroup:
    """Group of related tables for a domain"""
    name: str
    description: str
    relationships: List[Relationship] = field(default_factory=list)
    central_table: Optional[str] = None


class RelationshipConfig:
    """Configuration for table relationships"""
    
    def __init__(self):
        self.relationships: Dict[str, Relationship] = {}
        self.groups: Dict[str, RelationshipGroup] = {}
        self._load_default_relationships()
    
    def _load_default_relationships(self):
        """Load all default table relationships"""
        
        # ============================================================
        # User Domain
        # ============================================================
        user_group = RelationshipGroup(
            name="user_domain",
            description="User and person information",
            central_table="users"
        )
        
        # users -> person
        user_group.relationships.append(Relationship(
            name="users_to_person",
            from_table="users",
            to_table="person",
            relationship_type=RelationshipType.ONE_TO_ONE,
            from_field="personId",
            to_field="id",
            description="User to person details"
        ))
        
        # person -> countries
        user_group.relationships.append(Relationship(
            name="person_to_country",
            from_table="person",
            to_table="countries",
            relationship_type=RelationshipType.MANY_TO_ONE,
            from_field="countryId",
            to_field="id",
            description="Person's country"
        ))
        
        self.groups["user_domain"] = user_group
        
        # ============================================================
        # Project Domain
        # ============================================================
        project_group = RelationshipGroup(
            name="project_domain",
            description="Projects and assignments",
            central_table="projects"
        )
        
        # projects -> languages
        project_group.relationships.append(Relationship(
            name="project_to_language",
            from_table="projects",
            to_table="languages",
            relationship_type=RelationshipType.MANY_TO_ONE,
            from_field="languageId",
            to_field="id",
            description="Project language"
        ))
        
        # projects -> countries
        project_group.relationships.append(Relationship(
            name="project_to_country",
            from_table="projects",
            to_table="countries",
            relationship_type=RelationshipType.MANY_TO_ONE,
            from_field="countryId",
            to_field="id",
            description="Project country"
        ))
        
        # projects -> users_to_projects
        project_group.relationships.append(Relationship(
            name="project_to_assignments",
            from_table="projects",
            to_table="users_to_projects",
            relationship_type=RelationshipType.ONE_TO_MANY,
            from_field="id",
            to_field="projectId",
            description="Project assignments"
        ))
        
        self.groups["project_domain"] = project_group
        
        # ============================================================
        # Bible Translation Domain
        # ============================================================
        bible_group = RelationshipGroup(
            name="bible_domain",
            description="Bible translation content",
            central_table="text_translation_projects"
        )
        
        # text_translation_projects -> projects
        bible_group.relationships.append(Relationship(
            name="bible_proj_to_project",
            from_table="text_translation_projects",
            to_table="projects",
            relationship_type=RelationshipType.MANY_TO_ONE,
            from_field="projectId",
            to_field="id",
            description="Link to main projects table"
        ))
        
        # text_translation_projects -> text_translation_books
        bible_group.relationships.append(Relationship(
            name="bible_proj_to_books",
            from_table="text_translation_projects",
            to_table="text_translation_books",
            relationship_type=RelationshipType.ONE_TO_MANY,
            from_field="id",
            to_field="textTranslationProjectId",
            description="Books in project"
        ))
        
        # text_translation_books -> text_translation_chapters
        bible_group.relationships.append(Relationship(
            name="bible_books_to_chapters",
            from_table="text_translation_books",
            to_table="text_translation_chapters",
            relationship_type=RelationshipType.ONE_TO_MANY,
            from_field="id",
            to_field="textTranslationBookId",
            description="Chapters in book"
        ))
        
        self.groups["bible_domain"] = bible_group
        
        # ============================================================
        # OBS Domain
        # ============================================================
        obs_group = RelationshipGroup(
            name="obs_domain",
            description="OBS translation content",
            central_table="obs_projects"
        )
        
        # obs_projects -> projects
        obs_group.relationships.append(Relationship(
            name="obs_proj_to_project",
            from_table="obs_projects",
            to_table="projects",
            relationship_type=RelationshipType.MANY_TO_ONE,
            from_field="projectId",
            to_field="id",
            description="Link to main projects table"
        ))
        
        # obs_projects -> obs_project_chapters
        obs_group.relationships.append(Relationship(
            name="obs_proj_to_chapters",
            from_table="obs_projects",
            to_table="obs_project_chapters",
            relationship_type=RelationshipType.ONE_TO_MANY,
            from_field="id",
            to_field="obsProjectId",
            description="Chapters in project"
        ))
        
        # obs_project_chapters -> obs_audio_recordings
        obs_group.relationships.append(Relationship(
            name="obs_chapters_to_audio",
            from_table="obs_project_chapters",
            to_table="obs_audio_recordings",
            relationship_type=RelationshipType.ONE_TO_MANY,
            from_field="id",
            to_field="obsProjectChapterId",
            description="Audio recordings for chapter"
        ))
        
        self.groups["obs_domain"] = obs_group
        
        # ============================================================
        # Literature Domain
        # ============================================================
        literature_group = RelationshipGroup(
            name="literature_domain",
            description="Literature translation content",
            central_table="literature_projects"
        )
        
        # literature_projects -> projects
        literature_group.relationships.append(Relationship(
            name="lit_proj_to_project",
            from_table="literature_projects",
            to_table="projects",
            relationship_type=RelationshipType.MANY_TO_ONE,
            from_field="projectId",
            to_field="id",
            description="Link to main projects table"
        ))
        
        # literature_projects -> literature_project_genres
        literature_group.relationships.append(Relationship(
            name="lit_proj_to_genres",
            from_table="literature_projects",
            to_table="literature_project_genres",
            relationship_type=RelationshipType.ONE_TO_MANY,
            from_field="id",
            to_field="literatureProjectId",
            description="Genres in project"
        ))
        
        # literature_project_genres -> literature_project_genres_history
        literature_group.relationships.append(Relationship(
            name="lit_genres_to_history",
            from_table="literature_project_genres",
            to_table="literature_project_genres_history",
            relationship_type=RelationshipType.ONE_TO_MANY,
            from_field="id",
            to_field="literatureProjectGenreId",
            description="History records for genre"
        ))
        
        self.groups["literature_domain"] = literature_group
        
        # ============================================================
        # Grammar Domain
        # ============================================================
        grammar_group = RelationshipGroup(
            name="grammar_domain",
            description="Grammar translation content",
            central_table="grammar_phrases_projects"
        )
        
        # grammar_phrases_projects -> projects
        grammar_group.relationships.append(Relationship(
            name="grammar_proj_to_project",
            from_table="grammar_phrases_projects",
            to_table="projects",
            relationship_type=RelationshipType.MANY_TO_ONE,
            from_field="projectId",
            to_field="id",
            description="Link to main projects table"
        ))
        
        # grammar_phrases_projects -> grammar_phrases_project_contents
        grammar_group.relationships.append(Relationship(
            name="grammar_proj_to_contents",
            from_table="grammar_phrases_projects",
            to_table="grammar_phrases_project_contents",
            relationship_type=RelationshipType.ONE_TO_MANY,
            from_field="id",
            to_field="grammarPhrasesProjectId",
            description="Content versions"
        ))
        
        # grammar_phrases_project_contents -> grammar_phrases_project_content_history
        grammar_group.relationships.append(Relationship(
            name="grammar_contents_to_history",
            from_table="grammar_phrases_project_contents",
            to_table="grammar_phrases_project_content_history",
            relationship_type=RelationshipType.ONE_TO_MANY,
            from_field="id",
            to_field="grammarPhrasesProjectContentId",
            description="History records"
        ))
        
        self.groups["grammar_domain"] = grammar_group
        
        # Similar for pronouns and connectives (abbreviated)
        
        # ============================================================
        # Worklog Domain
        # ============================================================
        worklog_group = RelationshipGroup(
            name="worklog_domain",
            description="Worklog tracking",
            central_table="worklogs"
        )
        
        # worklogs -> users
        worklog_group.relationships.append(Relationship(
            name="worklog_to_user",
            from_table="worklogs",
            to_table="users",
            relationship_type=RelationshipType.MANY_TO_ONE,
            from_field="userId",
            to_field="id",
            description="User who did the work"
        ))
        
        # worklogs -> projects
        worklog_group.relationships.append(Relationship(
            name="worklog_to_project",
            from_table="worklogs",
            to_table="projects",
            relationship_type=RelationshipType.MANY_TO_ONE,
            from_field="projectId",
            to_field="id",
            description="Project worked on"
        ))
        
        self.groups["worklog_domain"] = worklog_group
        
        # Register all relationships in flat dictionary
        for group in self.groups.values():
            for rel in group.relationships:
                self.relationships[rel.name] = rel
    
    def get_relationship(self, name: str) -> Optional[Relationship]:
        """Get relationship by name"""
        return self.relationships.get(name)
    
    def get_relationships_for_table(self, table_name: str, direction: str = "both") -> List[Relationship]:
        """Get all relationships involving a table"""
        results = []
        for rel in self.relationships.values():
            if direction in ["both", "from"] and rel.from_table == table_name:
                results.append(rel)
            if direction in ["both", "to"] and rel.to_table == table_name:
                results.append(rel)
        return results
    
    def get_group(self, group_name: str) -> Optional[RelationshipGroup]:
        """Get relationship group by name"""
        return self.groups.get(group_name)
    
    def get_path_between_tables(self, from_table: str, to_table: str) -> Optional[List[Relationship]]:
        """Find a path between two tables (simple BFS)"""
        from collections import deque
        
        visited = set()
        queue = deque([(from_table, [])])
        
        while queue:
            current_table, path = queue.popleft()
            
            if current_table in visited:
                continue
            visited.add(current_table)
            
            # Get relationships from current table
            for rel in self.get_relationships_for_table(current_table):
                next_table = rel.to_table if rel.from_table == current_table else rel.from_table
                new_path = path + [rel]
                
                if next_table == to_table:
                    return new_path
                
                if next_table not in visited:
                    queue.append((next_table, new_path))
        
        return None
    
    def generate_join_chain(self, start_table: str, target_tables: List[str]) -> List[str]:
        """Generate SQL JOIN clauses to reach target tables"""
        joins = []
        visited_tables = {start_table}
        
        for target in target_tables:
            path = self.get_path_between_tables(start_table, target)
            if path:
                for rel in path:
                    if rel.from_table not in visited_tables or rel.to_table not in visited_tables:
                        # Determine join direction
                        if rel.from_table in visited_tables:
                            # Join from from_table to to_table
                            join_sql = f'LEFT JOIN {rel.to_table} ON {rel.from_table}.{rel.from_field} = {rel.to_table}.{rel.to_field}'
                            visited_tables.add(rel.to_table)
                        else:
                            # Join from to_table to from_table (reverse)
                            join_sql = f'LEFT JOIN {rel.from_table} ON {rel.to_table}.{rel.to_field} = {rel.from_table}.{rel.from_field}'
                            visited_tables.add(rel.from_table)
                        
                        if join_sql not in joins:
                            joins.append(join_sql)
        
        return joins


# Singleton instance
_relationship_config = None

def get_relationship_config() -> RelationshipConfig:
    """Get the singleton instance"""
    global _relationship_config
    if _relationship_config is None:
        _relationship_config = RelationshipConfig()
    return _relationship_config