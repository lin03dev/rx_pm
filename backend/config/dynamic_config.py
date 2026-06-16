"""
Dynamic Configuration Loader - Load all configurations from YAML/JSON files
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class DynamicConfig:
    """Dynamic configuration container"""
    config_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    
    # Config caches
    _book_mappings: Optional[Dict] = None
    _obs_config: Optional[Dict] = None
    _literature_genres: Optional[Dict] = None
    _stage_mappings: Optional[Dict] = None
    _project_types: Optional[Dict] = None
    
    def __post_init__(self):
        self.config_dir = Path(__file__).parent
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        file_path = self.config_dir / filename
        if file_path.exists():
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        file_path = self.config_dir / filename
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
    
    def save_json(self, filename: str, data: Dict[str, Any]):
        """Save JSON configuration file"""
        file_path = self.config_dir / filename
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_book_mappings(self) -> Dict[str, Any]:
        """Get book mapping configuration"""
        if self._book_mappings is None:
            self._book_mappings = self.load_json("book_mappings.json")
            if not self._book_mappings:
                self._book_mappings = self._get_default_book_mappings()
        return self._book_mappings
    
    def _get_default_book_mappings(self) -> Dict[str, Any]:
        """Get default book mappings"""
        return {
            "rules": [
                {
                    "type": "range",
                    "start": 101,
                    "end": 166,
                    "offset": -100,
                    "description": "Old Testament books"
                },
                {
                    "type": "range",
                    "start": 240,
                    "end": 266,
                    "offset": -200,
                    "description": "New Testament books"
                }
            ],
            "specific_mappings": {},
            "book_names": {
                "1": "Genesis", "2": "Exodus", "3": "Leviticus", "4": "Numbers",
                "5": "Deuteronomy", "6": "Joshua", "7": "Judges", "8": "Ruth",
                "9": "1 Samuel", "10": "2 Samuel", "11": "1 Kings", "12": "2 Kings",
                "13": "1 Chronicles", "14": "2 Chronicles", "15": "Ezra", "16": "Nehemiah",
                "17": "Esther", "18": "Job", "19": "Psalms", "20": "Proverbs",
                "21": "Ecclesiastes", "22": "Song of Solomon", "23": "Isaiah",
                "24": "Jeremiah", "25": "Lamentations", "26": "Ezekiel", "27": "Daniel",
                "28": "Hosea", "29": "Joel", "30": "Amos", "31": "Obadiah", "32": "Jonah",
                "33": "Micah", "34": "Nahum", "35": "Habakkuk", "36": "Zephaniah",
                "37": "Haggai", "38": "Zechariah", "39": "Malachi", "40": "Matthew",
                "41": "Mark", "42": "Luke", "43": "John", "44": "Acts", "45": "Romans",
                "46": "1 Corinthians", "47": "2 Corinthians", "48": "Galatians",
                "49": "Ephesians", "50": "Philippians", "51": "Colossians",
                "52": "1 Thessalonians", "53": "2 Thessalonians", "54": "1 Timothy",
                "55": "2 Timothy", "56": "Titus", "57": "Philemon", "58": "Hebrews",
                "59": "James", "60": "1 Peter", "61": "2 Peter", "62": "1 John",
                "63": "2 John", "64": "3 John", "65": "Jude", "66": "Revelation"
            }
        }
    
    def get_obs_config(self) -> Dict[str, Any]:
        """Get OBS configuration"""
        if self._obs_config is None:
            self._obs_config = self.load_json("obs_config.json")
            if not self._obs_config:
                self._obs_config = self._get_default_obs_config()
        return self._obs_config
    
    def _get_default_obs_config(self) -> Dict[str, Any]:
        """Get default OBS configuration"""
        return {
            "total_chapters": 50,
            "completion_thresholds": {
                "translation": 100,
                "audio": 100
            },
            "chapter_paragraphs": {
                "1": 16, "2": 12, "3": 16, "4": 9, "5": 12, "6": 14, "7": 10,
                "8": 14, "9": 15, "10": 12, "11": 8, "12": 14, "13": 15, "14": 12,
                "15": 13, "16": 13, "17": 14, "18": 15, "19": 18, "20": 13, "21": 13,
                "22": 7, "23": 10, "24": 9, "25": 13, "26": 10, "27": 11, "28": 10,
                "29": 9, "30": 9, "31": 14, "32": 17, "33": 15, "34": 12, "35": 16,
                "36": 12, "37": 15, "38": 17, "39": 15, "40": 13, "41": 12, "42": 10,
                "43": 18, "44": 17, "45": 13, "46": 12, "47": 13, "48": 18, "49": 18, "50": 15
            },
            "chapter_names": {
                "1": "The Creation", "2": "Sin Enters the World", "3": "The Flood",
                "4": "God's Covenant with Abraham", "5": "The Son of Promise",
                "6": "God Provides for Isaac", "7": "God Blesses Jacob",
                "8": "God Saves Joseph and His Family", "9": "God Calls Moses",
                "10": "The Ten Plagues", "11": "The Passover", "12": "The Exodus"
            }
        }
    
    def get_literature_genres(self) -> Dict[str, str]:
        """Get literature genre mappings"""
        if self._literature_genres is None:
            self._literature_genres = self.load_json("literature_genres.json")
            if not self._literature_genres:
                self._literature_genres = self._get_default_literature_genres()
        return self._literature_genres
    
    def _get_default_literature_genres(self) -> Dict[str, str]:
        """Get default literature genre mappings"""
        return {
            "childrens_literature": "Children's Literature",
            "formal_writing": "Formal Writing",
            "history": "History",
            "literature": "Literature",
            "narrative": "Narrative",
            "poetry": "Poetry"
        }
    
    def get_stage_mappings(self) -> Dict[str, str]:
        """Get stage code mappings"""
        if self._stage_mappings is None:
            self._stage_mappings = self.load_json("stage_mappings.json")
            if not self._stage_mappings:
                self._stage_mappings = self._get_default_stage_mappings()
        return self._stage_mappings
    
    def _get_default_stage_mappings(self) -> Dict[str, str]:
        """Get default stage mappings"""
        return {
            "1": "1.1 Recruitment / Benched",
            "2": "1.2 Preparation of Translation brief",
            "3": "1.3 Training and Drafting",
            "4": "2.1 Exegetical Checking",
            "5": "2.2 Basic and Advanced PT Checks",
            "6": "2.3 Projector/ Team Check",
            "7": "2.4 Back Translation",
            "8": "3.1 Community Checking",
            "9": "4.1 Update Back Translation",
            "10": "4.2 Consultant Checking",
            "11": "5.1 Read Aloud",
            "12": "5.3 Church / Community Leader Checking",
            "13": "5.4 Final Checks, publishing, engagement",
            "14": "5.2 Draft Recording",
            "obs.drafting": "OBS - Drafting",
            "obs.community_checking": "OBS - Community Checking",
            "obs.qa_check": "OBS - QA Check",
            "obs.read_aloud": "OBS - Read Aloud",
            "obs.recording": "OBS - Recording"
        }
    
    def get_project_type_configs(self) -> Dict[str, Dict]:
        """Get project type configurations"""
        if self._project_types is None:
            self._project_types = self.load_json("project_types.json")
            if not self._project_types:
                self._project_types = self._get_default_project_types()
        return self._project_types
    
    def _get_default_project_types(self) -> Dict[str, Dict]:
        """Get default project type configurations"""
        return {
            "TEXT_TRANSLATION": {
                "display_name": "Bible Translation",
                "icon": "📖",
                "content_table": "text_translation_chapters",
                "assignment_field": "verses",
                "analyzer": "bible_chapter"
            },
            "OBS": {
                "display_name": "Open Bible Stories",
                "icon": "📚",
                "content_table": "obs_project_chapters",
                "assignment_field": "obsChapters",
                "analyzer": "obs_chapter"
            },
            "LITERATURE": {
                "display_name": "Literature Translation",
                "icon": "📝",
                "content_table": "literature_project_genres",
                "assignment_field": "literatureGenres",
                "analyzer": "literature_block"
            },
            "LITERATURE_PROJECT": {
                "display_name": "Literature Project",
                "icon": "📝",
                "content_table": "literature_project_genres",
                "assignment_field": "literatureGenres",
                "analyzer": "literature_block"
            },
            "GRAMMAR_PHRASES": {
                "display_name": "Grammar - Phrases",
                "icon": "🔤",
                "content_table": "grammar_phrases_project_contents",
                "assignment_field": None,
                "analyzer": "generic_array",
                "item_key": "phrase"
            },
            "GRAMMAR_PRONOUNS": {
                "display_name": "Grammar - Pronouns",
                "icon": "👤",
                "content_table": "grammar_pronouns_project_contents",
                "assignment_field": None,
                "analyzer": "generic_array",
                "item_key": "pronoun"
            },
            "GRAMMAR_CONNECTIVES": {
                "display_name": "Grammar - Connectives",
                "icon": "🔗",
                "content_table": "grammar_connectives_project_contents",
                "assignment_field": None,
                "analyzer": "generic_array",
                "item_key": "connective"
            }
        }
    
    def reload_all(self):
        """Reload all configurations"""
        self._book_mappings = None
        self._obs_config = None
        self._literature_genres = None
        self._stage_mappings = None
        self._project_types = None


# Singleton instance
_dynamic_config = None

def get_dynamic_config() -> DynamicConfig:
    """Get singleton instance"""
    global _dynamic_config
    if _dynamic_config is None:
        _dynamic_config = DynamicConfig()
    return _dynamic_config
