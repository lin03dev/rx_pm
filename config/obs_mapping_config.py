"""
OBS Mapping Configuration - Dynamic configuration for OBS chapter assignments
"""

from typing import Dict, List, Set, Optional
import json
from pathlib import Path

class OBSMappingConfig:
    """Dynamic configuration for OBS chapter mapping"""
    
    def __init__(self, config_file: str = None):
        self.total_chapters = 50
        self.completion_version_threshold = 1
        self.chapter_paragraph_counts = {}
        self.chapter_names = {}
        self.audio_config = {
            'types': ['title', 'para'],
            'title_required': True,
            'para_audio_required': True,
            'track_individual_paragraphs': True,
            'completion_thresholds': {'translation': 100, 'audio': 100}
        }
        self.mtt_config = {
            'status_rules': {
                'completed': {'min_completion': 100, 'label': 'Completed'},
                'in_progress': {'min_completion': 1, 'max_completion': 99, 'label': 'In Progress'},
                'not_started': {'min_completion': 0, 'label': 'Not Started'}
            },
            'performance_ratings': {
                'excellent': {'min_completion': 90, 'color': 'green', 'icon': '🏆'},
                'good': {'min_completion': 70, 'color': 'blue', 'icon': '👍'},
                'average': {'min_completion': 50, 'color': 'orange', 'icon': '⭐'},
                'needs_improvement': {'min_completion': 25, 'color': 'yellow', 'icon': '⚠️'},
                'poor': {'min_completion': 0, 'color': 'red', 'icon': '❌'}
            }
        }
        self._load_defaults()
        if config_file:
            self._load_from_file(config_file)
    
    def _load_defaults(self):
        """Load default OBS configuration"""
        self.chapter_names = {
            1: "The Creation", 2: "Sin Enters the World", 3: "The Flood",
            4: "God's Covenant with Abraham", 5: "The Son of Promise",
            6: "God Provides for Isaac", 7: "God Blesses Jacob",
            8: "God Saves Joseph and His Family", 9: "God Calls Moses",
            10: "The Ten Plagues", 11: "The Passover", 12: "The Exodus",
            13: "God's Covenant with Israel", 14: "Wandering in the Wilderness",
            15: "The Promised Land", 16: "The Deliverers", 17: "God's Covenant with David",
            18: "The Divided Kingdom", 19: "The Prophets", 20: "The Exile and Return",
            21: "God Promises the Messiah", 22: "The Birth of John", 23: "The Birth of Jesus",
            24: "John Baptizes Jesus", 25: "Satan Tempts Jesus", 26: "Jesus Starts His Ministry",
            27: "The Story of the Good Samaritan", 28: "The Rich Young Ruler",
            29: "The Story of the Unmerciful Servant", 30: "Jesus Feeds Thousands of People",
            31: "Jesus Walks on Water", 32: "Jesus Heals a Demon-Possessed Man & a Sick Woman",
            33: "The Story of the Farmer", 34: "Jesus Teaches Other Stories",
            35: "The Story of the Compassionate Father", 36: "The Transfiguration",
            37: "Jesus Raises Lazarus from the Dead", 38: "Jesus Is Betrayed",
            39: "Jesus Is Put on Trial", 40: "Jesus Is Crucified", 41: "God Raises Jesus from the Dead",
            42: "Jesus Returns to Heaven", 43: "The Church Begins", 44: "Peter and John Heal a Beggar",
            45: "Stephen and Philip", 46: "Saul Becomes a Follower of Jesus",
            47: "Paul and Silas in Philippi", 48: "Jesus Is the Promised Messiah",
            49: "God's New Covenant", 50: "Jesus Returns"
        }
        
        self.chapter_paragraph_counts = {
            1: 16, 2: 12, 3: 16, 4: 9, 5: 12, 6: 14, 7: 10, 8: 14, 9: 15,
            10: 12, 11: 8, 12: 14, 13: 15, 14: 12, 15: 13, 16: 13, 17: 14,
            18: 15, 19: 18, 20: 13, 21: 13, 22: 7, 23: 10, 24: 9, 25: 13,
            26: 10, 27: 11, 28: 10, 29: 9, 30: 9, 31: 14, 32: 17, 33: 15,
            34: 12, 35: 16, 36: 12, 37: 15, 38: 17, 39: 15, 40: 13, 41: 12,
            42: 10, 43: 18, 44: 17, 45: 13, 46: 12, 47: 13, 48: 18, 49: 18, 50: 15
        }
    
    def _load_from_file(self, config_file: str):
        """Load OBS configuration from JSON file"""
        try:
            path = Path(config_file)
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                    if 'chapter_paragraph_counts' in data:
                        self.chapter_paragraph_counts.update({int(k): v for k, v in data['chapter_paragraph_counts'].items()})
        except Exception as e:
            print(f"⚠️ Could not load OBS config: {e}")
    
    def get_chapter_name(self, chapter_no: int) -> str:
        """Get the name of an OBS chapter"""
        return self.chapter_names.get(chapter_no, f"Chapter {chapter_no}")
    
    def get_chapter_paragraph_count(self, chapter_no: int) -> int:
        """Get the number of paragraphs in an OBS chapter"""
        return self.chapter_paragraph_counts.get(chapter_no, 0)
    
    def get_completion_thresholds(self) -> Dict:
        """Get completion thresholds for translation and audio"""
        return self.audio_config.get('completion_thresholds', {'translation': 100, 'audio': 100})
    
    def get_mtt_performance_rating(self, completion_pct: float) -> Dict:
        """Get performance rating based on completion percentage"""
        ratings = self.mtt_config.get('performance_ratings', {})
        for rating, rule in ratings.items():
            if completion_pct >= rule.get('min_completion', 0):
                return {
                    'rating': rating,
                    'icon': rule.get('icon', ''),
                    'color': rule.get('color', ''),
                    'label': rating.capitalize()
                }
        return {'rating': 'poor', 'icon': '❌', 'color': 'red', 'label': 'Poor'}
    
    def get_mtt_status(self, completion_pct: float) -> str:
        """Get MTT status based on completion percentage"""
        if completion_pct >= 100:
            return "Completed"
        elif completion_pct > 0:
            return "In Progress"
        return "Not Started"


# Singleton instance
_obs_mapping_config = None

def get_obs_mapping_config(config_file: str = None) -> OBSMappingConfig:
    """Get the singleton instance of OBSMappingConfig"""
    global _obs_mapping_config
    if _obs_mapping_config is None:
        _obs_mapping_config = OBSMappingConfig(config_file)
    return _obs_mapping_config


def parse_obs_assigned_chapters(chapters_string: str) -> Set[int]:
    """Parse assigned OBS chapters"""
    result = set()
    if not chapters_string:
        return result
    for ch in chapters_string.split(','):
        ch = ch.strip()
        if ch and ch.isdigit():
            result.add(int(ch))
    return result


def get_obs_chapter_name(chapter_no: int) -> str:
    """Get OBS chapter name"""
    return get_obs_mapping_config().get_chapter_name(chapter_no)


def get_obs_chapter_paragraph_count(chapter_no: int) -> int:
    """Get OBS chapter paragraph count"""
    return get_obs_mapping_config().get_chapter_paragraph_count(chapter_no)


def get_obs_audio_config() -> Dict:
    """Get OBS audio configuration"""
    return get_obs_mapping_config().audio_config


def get_obs_mtt_config() -> Dict:
    """Get OBS MTT configuration"""
    return get_obs_mapping_config().mtt_config