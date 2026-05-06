"""
Unified Completion Calculator - Centralized metrics calculation for all project types
"""

from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.content_analyzer import ContentAnalyzer, AnalyzerFactory, ContentMetrics


class CompletionStatus(Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    NOT_STARTED = "not_started"
    NO_MTT = "no_mtt"


@dataclass
class ProjectCompletion:
    """Completion data for a project"""
    project_id: str
    project_name: str
    project_type: str
    total_assigned: int = 0
    total_completed: int = 0
    completion_pct: float = 0.0
    status: CompletionStatus = CompletionStatus.NOT_STARTED
    mtt_count: int = 0
    mtt_names: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MTTCompletion:
    """Completion data for an MTT"""
    user_id: str
    username: str
    full_name: str
    project_id: str
    project_name: str
    total_assigned: int = 0
    total_completed: int = 0
    completion_pct: float = 0.0
    status: CompletionStatus = CompletionStatus.NOT_STARTED
    assigned_items: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CompletionCalculator:
    """Unified calculator for project completion metrics"""
    
    def __init__(self, db_manager, config: Optional[Dict] = None):
        self.db_manager = db_manager
        self.config = config or {}
        self.analyzers: Dict[str, ContentAnalyzer] = {}
    
    def get_analyzer(self, project_type: str) -> ContentAnalyzer:
        """Get or create analyzer for project type"""
        if project_type not in self.analyzers:
            self.analyzers[project_type] = AnalyzerFactory.get_analyzer(project_type)
        return self.analyzers[project_type]
    
    def parse_assigned_items(self, assigned_string: str, project_type: str) -> Set[str]:
        """Parse assigned items based on project type"""
        if not assigned_string:
            return set()
        
        items = set()
        for item in assigned_string.split(','):
            item = item.strip()
            if item:
                if project_type == 'OBS' and item.isdigit():
                    items.add(f"ch_{int(item):03d}")
                elif project_type == 'TEXT_TRANSLATION' and len(item) >= 6:
                    items.add(item)
                else:
                    items.add(item)
        return items
    
    def calculate_project_completion(self, project_id: str, project_type: str,
                                      assigned_items: Set[str]) -> ProjectCompletion:
        """Calculate completion for a single project"""
        result = ProjectCompletion(
            project_id=project_id,
            project_type=project_type,
            project_name="",
            total_assigned=len(assigned_items)
        )
        
        if not assigned_items:
            return result
        
        # This would need to be implemented per project type
        # For now, returns placeholder
        return result
    
    def get_status(self, completion_pct: float, has_mtt: bool = True) -> CompletionStatus:
        """Get status based on completion percentage"""
        if not has_mtt:
            return CompletionStatus.NO_MTT
        elif completion_pct >= 100:
            return CompletionStatus.COMPLETED
        elif completion_pct > 0:
            return CompletionStatus.IN_PROGRESS
        else:
            return CompletionStatus.NOT_STARTED
    
    def get_status_label(self, status: CompletionStatus) -> str:
        """Get human-readable status label"""
        labels = {
            CompletionStatus.COMPLETED: "✅ Completed",
            CompletionStatus.IN_PROGRESS: "🟢 In Progress",
            CompletionStatus.NOT_STARTED: "⚪ Not Started",
            CompletionStatus.NO_MTT: "⚠️ No MTT Assigned"
        }
        return labels.get(status, "Unknown")
    
    def get_performance_rating(self, completion_pct: float) -> Dict[str, Any]:
        """Get performance rating based on completion percentage"""
        if completion_pct >= 100:
            return {"rating": "excellent", "label": "🏆 Excellent", "color": "green"}
        elif completion_pct >= 75:
            return {"rating": "good", "label": "👍 Good", "color": "blue"}
        elif completion_pct >= 50:
            return {"rating": "average", "label": "⭐ Average", "color": "orange"}
        elif completion_pct >= 25:
            return {"rating": "needs_improvement", "label": "⚠️ Needs Improvement", "color": "yellow"}
        elif completion_pct > 0:
            return {"rating": "poor", "label": "📝 Just Started", "color": "cyan"}
        else:
            return {"rating": "not_started", "label": "❌ Not Started", "color": "red"}


class ProjectCompletionCalculator(CompletionCalculator):
    """Specialized calculator for Bible project completion"""
    
    def __init__(self, db_manager, config: Optional[Dict] = None):
        super().__init__(db_manager, config)
        self.book_mapping = self._load_book_mapping()
    
    def _load_book_mapping(self) -> Dict[int, int]:
        """Load book mapping from config"""
        mapping = {}
        # OT: 101-166 → 1-66
        for i in range(101, 167):
            mapping[i] = i - 100
        # NT: 240-266 → 40-66
        for i in range(240, 267):
            mapping[i] = i - 200
        return mapping
    
    def map_assigned_verse(self, verse_id: str) -> Optional[str]:
        """Map assigned verse to standard format"""
        if not verse_id or len(verse_id) < 9:
            return None
        
        try:
            book = int(verse_id[:3])
            chapter = int(verse_id[3:6])
            verse = int(verse_id[6:9])
            
            mapped_book = self.book_mapping.get(book, book)
            return f"{mapped_book:03d}{chapter:03d}{verse:03d}"
        except:
            return None
    
    def get_assigned_verses(self, verses_string: str) -> Set[str]:
        """Get set of assigned verses"""
        result = set()
        if not verses_string:
            return result
        
        for verse_id in verses_string.split(','):
            verse_id = verse_id.strip()
            if verse_id:
                mapped = self.map_assigned_verse(verse_id)
                if mapped:
                    result.add(mapped)
        return result


class OBSCompletionCalculator(CompletionCalculator):
    """Specialized calculator for OBS project completion"""
    
    def __init__(self, db_manager, config: Optional[Dict] = None):
        super().__init__(db_manager, config)
        self._load_chapter_config()
    
    def _load_chapter_config(self):
        """Load OBS chapter configuration"""
        # Default paragraph counts
        self.chapter_paragraphs = {
            1: 16, 2: 12, 3: 16, 4: 9, 5: 12, 6: 14, 7: 10, 8: 14, 9: 15,
            10: 12, 11: 8, 12: 14, 13: 15, 14: 12, 15: 13, 16: 13, 17: 14,
            18: 15, 19: 18, 20: 13, 21: 13, 22: 7, 23: 10, 24: 9, 25: 13,
            26: 10, 27: 11, 28: 10, 29: 9, 30: 9, 31: 14, 32: 17, 33: 15,
            34: 12, 35: 16, 36: 12, 37: 15, 38: 17, 39: 15, 40: 13, 41: 12,
            42: 10, 43: 18, 44: 17, 45: 13, 46: 12, 47: 13, 48: 18, 49: 18, 50: 15
        }
        
        # Chapter names
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
            29: "The Story of the Unmerciful Servant", 30: "Jesus Feeds Thousands",
            31: "Jesus Walks on Water", 32: "Jesus Heals", 33: "The Story of the Farmer",
            34: "Jesus Teaches Other Stories", 35: "The Compassionate Father",
            36: "The Transfiguration", 37: "Jesus Raises Lazarus", 38: "Jesus Is Betrayed",
            39: "Jesus Is Put on Trial", 40: "Jesus Is Crucified", 41: "Jesus Rises",
            42: "Jesus Returns to Heaven", 43: "The Church Begins", 44: "Peter and John",
            45: "Stephen and Philip", 46: "Saul Becomes a Follower", 47: "Paul and Silas",
            48: "Jesus Is the Promised Messiah", 49: "God's New Covenant", 50: "Jesus Returns"
        }
    
    def get_chapter_paragraph_count(self, chapter_no: int) -> int:
        """Get paragraph count for a chapter"""
        return self.chapter_paragraphs.get(chapter_no, 0)
    
    def get_chapter_name(self, chapter_no: int) -> str:
        """Get chapter name"""
        return self.chapter_names.get(chapter_no, f"Chapter {chapter_no}")
    
    def parse_assigned_chapters(self, chapters_string: str) -> Set[int]:
        """Parse assigned OBS chapters"""
        result = set()
        if not chapters_string:
            return result
        
        for ch in chapters_string.split(','):
            ch = ch.strip()
            if ch and ch.isdigit():
                result.add(int(ch))
        return result
