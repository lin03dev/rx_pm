"""
Book Mapping Configuration - Dynamic mapping between assigned book numbers and standard Bible books
"""

from typing import Dict, Tuple, Optional, List
import json
from pathlib import Path

class BookMappingConfig:
    """Dynamic configuration for book ID mappings"""
    
    def __init__(self, config_file: str = None):
        self.mappings = {}
        self.rules = []
        self.specific_mappings = {}
        self._load_default_mappings()
        if config_file:
            self._load_from_file(config_file)
    
    def _load_default_mappings(self):
        """Load default book mappings"""
        self.rules = [
            {'type': 'range', 'start': 101, 'end': 166, 'offset': -100, 'description': 'Old Testament books (Genesis to Malachi)'},
            {'type': 'range', 'start': 240, 'end': 266, 'offset': -200, 'description': 'New Testament books (Matthew to Revelation)'},
        ]
        
        self.specific_mappings = {}
        
        # Book name mappings
        self.book_names = {
            1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
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
            61: "2 Peter", 62: "1 John", 63: "2 John", 64: "3 John", 65: "Jude", 66: "Revelation"
        }
    
    def _load_from_file(self, config_file: str):
        """Load mappings from JSON configuration file"""
        try:
            path = Path(config_file)
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                    if 'rules' in data:
                        self.rules = data['rules']
                    if 'specific_mappings' in data:
                        self.specific_mappings.update(data['specific_mappings'])
        except Exception as e:
            print(f"⚠️ Could not load config file: {e}")
    
    def map_book(self, assigned_book: int) -> int:
        """Map an assigned book number to standard Bible book number"""
        if assigned_book in self.specific_mappings:
            return self.specific_mappings[assigned_book]
        
        for rule in self.rules:
            if rule['type'] == 'range':
                if rule['start'] <= assigned_book <= rule['end']:
                    return assigned_book + rule['offset']
        
        return assigned_book
    
    def map_verse_id(self, verse_id: str) -> str:
        """Map an entire verse ID (BBBCCCVVV format)"""
        try:
            if len(verse_id) >= 9:
                book = int(verse_id[:3])
                chapter = int(verse_id[3:6])
                verse = int(verse_id[6:9])
                mapped_book = self.map_book(book)
                return f"{mapped_book:03d}{chapter:03d}{verse:03d}"
        except:
            pass
        return verse_id
    
    def get_book_name(self, book_number: int) -> str:
        """Get the English name of a Bible book"""
        return self.book_names.get(book_number, f"Book {book_number}")
    
    def get_all_mappings(self) -> Dict[int, int]:
        """Get all book mappings as a dictionary"""
        mappings = {}
        mappings.update(self.specific_mappings)
        for rule in self.rules:
            if rule['type'] == 'range':
                for book in range(rule['start'], rule['end'] + 1):
                    mappings[book] = book + rule['offset']
        return mappings


# Singleton instance
_book_mapping_config = None

def get_book_mapping_config(config_file: str = None) -> BookMappingConfig:
    """Get the singleton instance of BookMappingConfig"""
    global _book_mapping_config
    if _book_mapping_config is None:
        _book_mapping_config = BookMappingConfig(config_file)
    return _book_mapping_config


def map_book(assigned_book: int) -> int:
    """Convenience function to map a book number"""
    return get_book_mapping_config().map_book(assigned_book)


def map_verse_id(verse_id: str) -> str:
    """Convenience function to map a verse ID"""
    return get_book_mapping_config().map_verse_id(verse_id)


def get_book_name(book_number: int) -> str:
    """Convenience function to get book name"""
    return get_book_mapping_config().get_book_name(book_number)