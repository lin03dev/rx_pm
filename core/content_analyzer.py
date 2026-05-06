"""
Content Analyzer - Generic JSON content analysis for all project types
"""

import json
import re
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ContentMetrics:
    """Standard metrics for content analysis"""
    total_items: int = 0
    completed_items: int = 0
    completion_pct: float = 0.0
    has_content: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContentAnalyzer(ABC):
    """Abstract base class for content analyzers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def analyze(self, content: Any) -> ContentMetrics:
        """Analyze content and return metrics"""
        pass
    
    @abstractmethod
    def get_item_key(self) -> str:
        """Get the key used to identify items in JSON"""
        pass
    
    def _parse_json(self, content: Any) -> Optional[Dict]:
        """Parse JSON content safely"""
        if content is None:
            return None
        try:
            if isinstance(content, str):
                return json.loads(content)
            return content
        except:
            return None


class GenericArrayAnalyzer(ContentAnalyzer):
    """Analyzer for simple array-based content (Grammar, etc.)"""
    
    def __init__(self, item_key: str, array_path: str = "content", config: Optional[Dict] = None):
        super().__init__(config)
        self._item_key = item_key
        self._array_path = array_path
    
    def get_item_key(self) -> str:
        return self._item_key
    
    def analyze(self, content: Any) -> ContentMetrics:
        metrics = ContentMetrics()
        data = self._parse_json(content)
        
        if not data:
            return metrics
        
        # Navigate to array
        current = data
        for path_part in self._array_path.split('.'):
            if isinstance(current, dict):
                current = current.get(path_part, [])
            else:
                break
        
        if not isinstance(current, list):
            return metrics
        
        metrics.total_items = len(current)
        metrics.completed_items = sum(
            1 for item in current 
            if isinstance(item, dict) and item.get(self._item_key, '').strip()
        )
        
        if metrics.total_items > 0:
            metrics.completion_pct = (metrics.completed_items / metrics.total_items) * 100
        
        metrics.has_content = metrics.completed_items > 0
        
        return metrics


class OBSChapterAnalyzer(ContentAnalyzer):
    """Analyzer for OBS chapter content"""
    
    def get_item_key(self) -> str:
        return "content"
    
    def analyze(self, content: Any) -> ContentMetrics:
        metrics = ContentMetrics()
        data = self._parse_json(content)
        
        if not data:
            return metrics
        
        # Check title
        title = data.get('title', '')
        title_completed = 1 if title and title.strip() else 0
        
        # Check bibleRef
        bible_ref = data.get('bibleRef', '')
        bible_ref_completed = 1 if bible_ref and bible_ref.strip() else 0
        
        # Check paragraphs
        paras = data.get('paras', [])
        total_paras = len(paras)
        completed_paras = sum(
            1 for p in paras 
            if isinstance(p, dict) and p.get('content', '').strip()
        )
        
        metrics.total_items = 2 + total_paras
        metrics.completed_items = title_completed + bible_ref_completed + completed_paras
        
        if metrics.total_items > 0:
            metrics.completion_pct = (metrics.completed_items / metrics.total_items) * 100
        
        metrics.has_content = metrics.completed_items > 0
        metrics.metadata = {
            'title_completed': title_completed,
            'bible_ref_completed': bible_ref_completed,
            'total_paras': total_paras,
            'completed_paras': completed_paras
        }
        
        return metrics


class LiteratureBlockAnalyzer(ContentAnalyzer):
    """Analyzer for literature block-based content"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._sentence_pattern = re.compile(r'[.!?]+')
    
    def get_item_key(self) -> str:
        return "content"
    
    def _count_sentences(self, text: str) -> int:
        """Count number of sentences in text"""
        if not text:
            return 0
        sentences = self._sentence_pattern.split(text)
        return len([s for s in sentences if s.strip()])
    
    def analyze(self, content: Any) -> ContentMetrics:
        metrics = ContentMetrics()
        data = self._parse_json(content)
        
        if not data:
            return metrics
        
        blocks = data.get('content', [])
        if not isinstance(blocks, list):
            return metrics
        
        metrics.total_items = len(blocks)
        
        total_sentences = 0
        total_words = 0
        total_chars = 0
        
        for block in blocks:
            if isinstance(block, dict):
                text = block.get('content', '')
                if text and text.strip():
                    metrics.completed_items += 1
                    total_sentences += self._count_sentences(text)
                    total_words += len(text.split())
                    total_chars += len(text)
        
        if metrics.total_items > 0:
            metrics.completion_pct = (metrics.completed_items / metrics.total_items) * 100
        
        metrics.has_content = metrics.completed_items > 0
        metrics.metadata = {
            'total_sentences': total_sentences,
            'total_words': total_words,
            'total_characters': total_chars
        }
        
        return metrics


class BibleChapterAnalyzer(ContentAnalyzer):
    """Analyzer for Bible chapter content"""
    
    def get_item_key(self) -> str:
        return "text"
    
    def analyze(self, content: Any) -> ContentMetrics:
        metrics = ContentMetrics()
        data = self._parse_json(content)
        
        if not data:
            return metrics
        
        verses = data.get('content', [])
        if not isinstance(verses, list):
            return metrics
        
        metrics.total_items = len(verses)
        
        for verse in verses:
            if isinstance(verse, dict):
                text = verse.get('text', '')
                if text and text.strip():
                    metrics.completed_items += 1
        
        if metrics.total_items > 0:
            metrics.completion_pct = (metrics.completed_items / metrics.total_items) * 100
        
        metrics.has_content = metrics.completed_items > 0
        
        return metrics


class AnalyzerFactory:
    """Factory for creating content analyzers"""
    
    _analyzers: Dict[str, type] = {
        'TEXT_TRANSLATION': BibleChapterAnalyzer,
        'OBS': OBSChapterAnalyzer,
        'LITERATURE': LiteratureBlockAnalyzer,
        'LITERATURE_PROJECT': LiteratureBlockAnalyzer,
        'GRAMMAR_PHRASES': lambda: GenericArrayAnalyzer('phrase'),
        'GRAMMAR_PRONOUNS': lambda: GenericArrayAnalyzer('pronoun'),
        'GRAMMAR_CONNECTIVES': lambda: GenericArrayAnalyzer('connective'),
    }
    
    @classmethod
    def get_analyzer(cls, project_type: str, config: Optional[Dict] = None) -> ContentAnalyzer:
        """Get analyzer for project type"""
        analyzer_class = cls._analyzers.get(project_type)
        
        if analyzer_class:
            # Handle callable that returns instance vs class
            if callable(analyzer_class) and not isinstance(analyzer_class, type):
                return analyzer_class()
            return analyzer_class(config)
        
        # Default analyzer
        return GenericArrayAnalyzer('content', config=config)
    
    @classmethod
    def register_analyzer(cls, project_type: str, analyzer_class: type):
        """Register a custom analyzer"""
        cls._analyzers[project_type] = analyzer_class
