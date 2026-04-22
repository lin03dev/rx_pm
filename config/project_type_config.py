"""
Project Type Configuration - Dynamic configuration for all project types
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class ProjectType(str, Enum):
    """All project types in the system"""
    TEXT_TRANSLATION = "TEXT_TRANSLATION"
    OBS = "OBS"
    LITERATURE = "LITERATURE"
    LITERATURE_PROJECT = "LITERATURE_PROJECT"
    GRAMMAR_PHRASES = "GRAMMAR_PHRASES"
    GRAMMAR_PRONOUNS = "GRAMMAR_PRONOUNS"
    GRAMMAR_CONNECTIVES = "GRAMMAR_CONNECTIVES"


@dataclass
class ContentTableConfig:
    """Configuration for content storage table"""
    table_name: str
    project_link_field: str  # Field linking to project
    content_field: str
    version_field: str
    user_id_field: Optional[str] = None
    history_table: Optional[str] = None
    content_type: str = "json"  # json, text, structured
    
    # For JSON content extraction
    json_paths: Dict[str, str] = field(default_factory=dict)
    # e.g., {"verses": "$.content[*].text", "paragraphs": "$.paras[*].content"}


@dataclass
class AssignmentTableConfig:
    """Configuration for assignment storage"""
    table_name: str = "users_to_projects"
    user_id_field: str = "userId"
    project_id_field: str = "projectId"
    role_field: str = "role"
    
    # Assignment fields per project type
    assignment_fields: Dict[str, str] = field(default_factory=lambda: {
        ProjectType.TEXT_TRANSLATION: "verses",
        ProjectType.OBS: "obsChapters",
        ProjectType.LITERATURE: "literatureGenres",
        ProjectType.LITERATURE_PROJECT: "literatureGenres",
        ProjectType.GRAMMAR_PHRASES: None,  # No specific assignment field
        ProjectType.GRAMMAR_PRONOUNS: None,
        ProjectType.GRAMMAR_CONNECTIVES: None,
    })
    
    # For parsing assignments
    field_separator: str = ","
    value_type: str = "string"  # string, json, range


@dataclass
class CompletionMetrics:
    """Metrics for tracking completion"""
    metrics: List[Dict[str, Any]] = field(default_factory=list)
    # Each metric: {
    #   "name": "verses_completed",
    #   "label": "Verses Completed",
    #   "source": "content_json_path",
    #   "calculation": "count" or "sum",
    #   "threshold": 100
    # }


@dataclass
class ProjectTypeConfig:
    """Complete configuration for a project type"""
    name: str
    display_name: str
    project_type_enum: ProjectType
    
    # Content tables
    content_table: ContentTableConfig
    
    # Assignment configuration
    assignment: AssignmentTableConfig = field(default_factory=AssignmentTableConfig)
    
    # Completion metrics
    completion_metrics: CompletionMetrics = field(default_factory=CompletionMetrics)
    
    # Performance rating configuration
    performance_ratings: Dict[str, Dict] = field(default_factory=lambda: {
        "excellent": {"min": 100, "icon": "🏆", "label": "Excellent"},
        "good": {"min": 75, "icon": "👍", "label": "Good"},
        "average": {"min": 50, "icon": "⭐", "label": "Average"},
        "needs_improvement": {"min": 25, "icon": "⚠️", "label": "Needs Improvement"},
        "poor": {"min": 0, "icon": "❌", "label": "Poor"}
    })
    
    # Status rules
    status_rules: Dict[str, Dict] = field(default_factory=lambda: {
        "completed": {"min_completion": 100, "requires_content": True},
        "in_progress": {"min_completion": 1, "max_completion": 99},
        "not_started": {"min_completion": 0, "requires_assignment": True},
        "no_mtt": {"requires_assignment": False}
    })
    
    # Additional metadata
    description: str = ""
    icon: str = "📄"
    enabled: bool = True


# ============================================================
# Project Type Configurations
# ============================================================

def get_text_translation_config() -> ProjectTypeConfig:
    """Configuration for Bible text translation projects"""
    
    content_config = ContentTableConfig(
        table_name="text_translation_chapters",
        project_link_field="textTranslationBookId->textTranslationProjectId",
        content_field="content",
        version_field="version",
        user_id_field=None,  # No direct userId in content table
        content_type="json",
        json_paths={
            "verses": "$.content[*].text",
            "verse_numbers": "$.content[*].start",
            "chapter": "$.chapter",
            "book": "$.book"
        }
    )
    
    completion_metrics = CompletionMetrics(
        metrics=[
            {
                "name": "chapters_completed",
                "label": "Chapters Completed",
                "source": "content_table",
                "calculation": "count_distinct",
                "group_by": ["projectId", "book", "chapter"],
                "threshold": 100
            },
            {
                "name": "verses_completed",
                "label": "Verses Completed",
                "source": "json_content",
                "json_path": "$.content[*].text",
                "calculation": "count_non_empty",
                "threshold": 100
            }
        ]
    )
    
    return ProjectTypeConfig(
        name="text_translation",
        display_name="Bible Translation",
        project_type_enum=ProjectType.TEXT_TRANSLATION,
        content_table=content_config,
        completion_metrics=completion_metrics,
        description="Bible verse and chapter translation projects",
        icon="📖"
    )


def get_obs_config() -> ProjectTypeConfig:
    """Configuration for OBS (Open Bible Stories) projects"""
    
    content_config = ContentTableConfig(
        table_name="obs_project_chapters",
        project_link_field="obsProjectId",
        content_field="data",
        version_field="version",
        user_id_field=None,
        history_table=None,
        content_type="json",
        json_paths={
            "title": "$.title",
            "bible_ref": "$.bibleRef",
            "paragraphs": "$.paras[*].content",
            "paragraph_count": "$.paras.length",
            "completed_paragraphs": "$.paras[?(@.content != '')]"
        }
    )
    
    completion_metrics = CompletionMetrics(
        metrics=[
            {
                "name": "chapters_completed",
                "label": "Chapters Completed",
                "source": "content_table",
                "calculation": "count_distinct",
                "group_by": ["projectId", "chapterNo"],
                "threshold": 100
            },
            {
                "name": "titles_completed",
                "label": "Titles Completed",
                "source": "json_content",
                "json_path": "$.title",
                "calculation": "count_non_empty",
                "threshold": 100
            },
            {
                "name": "biblerefs_completed",
                "label": "Bible References Completed",
                "source": "json_content",
                "json_path": "$.bibleRef",
                "calculation": "count_non_empty",
                "threshold": 100
            },
            {
                "name": "paragraphs_completed",
                "label": "Paragraphs Completed",
                "source": "json_content",
                "json_path": "$.paras[*].content",
                "calculation": "count_non_empty",
                "threshold": 100
            }
        ]
    )
    
    return ProjectTypeConfig(
        name="obs",
        display_name="Open Bible Stories",
        project_type_enum=ProjectType.OBS,
        content_table=content_config,
        completion_metrics=completion_metrics,
        description="OBS chapter translation with title, Bible references, and paragraphs",
        icon="📚"
    )


def get_literature_config() -> ProjectTypeConfig:
    """Configuration for Literature projects"""
    
    content_config = ContentTableConfig(
        table_name="literature_project_genres",
        project_link_field="literatureProjectId",
        content_field="content",
        version_field="version",
        user_id_field=None,
        history_table="literature_project_genres_history",
        content_type="json",
        json_paths={
            "sections": "$.content[*].content",
            "section_titles": "$.content[*].title",
            "word_count": "text_length"
        }
    )
    
    completion_metrics = CompletionMetrics(
        metrics=[
            {
                "name": "genres_completed",
                "label": "Genres Completed",
                "source": "content_table",
                "calculation": "count_distinct",
                "group_by": ["projectId", "genreId"],
                "threshold": 100
            },
            {
                "name": "has_meaningful_content",
                "label": "Has Meaningful Content",
                "source": "json_content",
                "json_path": "$.content[*].content",
                "calculation": "has_non_empty",
                "threshold": 100
            },
            {
                "name": "word_count",
                "label": "Word Count",
                "source": "calculated",
                "calculation": "sum_word_count",
                "threshold": 100
            }
        ]
    )
    
    return ProjectTypeConfig(
        name="literature",
        display_name="Literature Translation",
        project_type_enum=ProjectType.LITERATURE,
        content_table=content_config,
        completion_metrics=completion_metrics,
        description="Literature genre translation projects with content quality tracking",
        icon="📝"
    )


def get_grammar_config(grammar_type: ProjectType) -> ProjectTypeConfig:
    """Configuration for Grammar projects (phrases, pronouns, connectives)"""
    
    table_map = {
        ProjectType.GRAMMAR_PHRASES: {
            "content": "grammar_phrases_project_contents",
            "project": "grammar_phrases_projects",
            "history": "grammar_phrases_project_content_history",
            "content_field": "content",
            "json_path": "$.phrases[*].phrase"
        },
        ProjectType.GRAMMAR_PRONOUNS: {
            "content": "grammar_pronouns_project_contents",
            "project": "grammar_pronouns_projects",
            "history": "grammar_pronouns_project_content_history",
            "content_field": "content",
            "json_path": "$.pronouns[*].pronoun"
        },
        ProjectType.GRAMMAR_CONNECTIVES: {
            "content": "grammar_connectives_project_contents",
            "project": "grammar_connectives_projects",
            "history": "grammar_connectives_project_content_history",
            "content_field": "content",
            "json_path": "$.connectives[*].connective"
        }
    }
    
    mapping = table_map[grammar_type]
    
    content_config = ContentTableConfig(
        table_name=mapping["content"],
        project_link_field="grammarPhrasesProjectId",
        content_field=mapping["content_field"],
        version_field="version",
        user_id_field="userId",
        history_table=mapping["history"],
        content_type="json",
        json_paths={
            "items": mapping["json_path"],
            "has_content": f"{mapping['json_path']}[?(@ != '')]"
        }
    )
    
    completion_metrics = CompletionMetrics(
        metrics=[
            {
                "name": "items_completed",
                "label": "Grammar Items Completed",
                "source": "json_content",
                "json_path": mapping["json_path"],
                "calculation": "count_non_empty",
                "threshold": 100
            }
        ]
    )
    
    display_names = {
        ProjectType.GRAMMAR_PHRASES: "Grammar Phrases",
        ProjectType.GRAMMAR_PRONOUNS: "Grammar Pronouns",
        ProjectType.GRAMMAR_CONNECTIVES: "Grammar Connectives"
    }
    
    icons = {
        ProjectType.GRAMMAR_PHRASES: "🔤",
        ProjectType.GRAMMAR_PRONOUNS: "👤",
        ProjectType.GRAMMAR_CONNECTIVES: "🔗"
    }
    
    return ProjectTypeConfig(
        name=grammar_type.value.lower(),
        display_name=display_names[grammar_type],
        project_type_enum=grammar_type,
        content_table=content_config,
        completion_metrics=completion_metrics,
        description=f"{display_names[grammar_type]} translation projects",
        icon=icons[grammar_type]
    )


# ============================================================
# Configuration Manager
# ============================================================

class ProjectTypeConfigManager:
    """Manager for all project type configurations"""
    
    def __init__(self, config_file: str = None):
        self.configs: Dict[ProjectType, ProjectTypeConfig] = {}
        self._load_default_configs()
        if config_file:
            self._load_from_file(config_file)
    
    def _load_default_configs(self):
        """Load all default configurations"""
        self.configs[ProjectType.TEXT_TRANSLATION] = get_text_translation_config()
        self.configs[ProjectType.OBS] = get_obs_config()
        self.configs[ProjectType.LITERATURE] = get_literature_config()
        self.configs[ProjectType.LITERATURE_PROJECT] = get_literature_config()
        self.configs[ProjectType.GRAMMAR_PHRASES] = get_grammar_config(ProjectType.GRAMMAR_PHRASES)
        self.configs[ProjectType.GRAMMAR_PRONOUNS] = get_grammar_config(ProjectType.GRAMMAR_PRONOUNS)
        self.configs[ProjectType.GRAMMAR_CONNECTIVES] = get_grammar_config(ProjectType.GRAMMAR_CONNECTIVES)
    
    def _load_from_file(self, config_file: str):
        """Load configurations from JSON file"""
        try:
            path = Path(config_file)
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                    # Override configurations from file
                    # (Implementation for custom overrides)
                    print(f"✅ Loaded project type configs from {config_file}")
        except Exception as e:
            print(f"⚠️ Could not load config file: {e}")
    
    def save_to_file(self, config_file: str):
        """Save configurations to JSON file"""
        data = {}
        for ptype, config in self.configs.items():
            data[ptype.value] = {
                "name": config.name,
                "display_name": config.display_name,
                "description": config.description,
                "icon": config.icon,
                "enabled": config.enabled
            }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved project type configs to {config_file}")
    
    def get_config(self, project_type: ProjectType) -> Optional[ProjectTypeConfig]:
        """Get configuration for a project type"""
        return self.configs.get(project_type)
    
    def get_config_by_name(self, name: str) -> Optional[ProjectTypeConfig]:
        """Get configuration by name"""
        for config in self.configs.values():
            if config.name == name or config.display_name == name:
                return config
        return None
    
    def get_config_by_enum(self, project_type_enum: str) -> Optional[ProjectTypeConfig]:
        """Get configuration by enum string value"""
        try:
            ptype = ProjectType(project_type_enum)
            return self.configs.get(ptype)
        except ValueError:
            return None
    
    def get_all_enabled(self) -> List[ProjectTypeConfig]:
        """Get all enabled configurations"""
        return [c for c in self.configs.values() if c.enabled]
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported project type names"""
        return [c.name for c in self.configs.values() if c.enabled]


# Singleton instance
_project_type_config_manager = None

def get_project_type_config_manager(config_file: str = None) -> ProjectTypeConfigManager:
    """Get the singleton instance"""
    global _project_type_config_manager
    if _project_type_config_manager is None:
        _project_type_config_manager = ProjectTypeConfigManager(config_file)
    return _project_type_config_manager


def get_project_type_config(project_type: ProjectType) -> Optional[ProjectTypeConfig]:
    """Convenience function to get config by enum"""
    return get_project_type_config_manager().get_config(project_type)