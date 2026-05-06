"""
Book Mapping Config - Backward compatibility layer that uses dynamic config
"""

from config.dynamic_config import get_dynamic_config

def get_book_mapping_config():
    return get_dynamic_config().get_book_mappings()

def map_book(book_num):
    """Map assigned book number to standard Bible book number"""
    if 101 <= book_num <= 166:
        return book_num - 100
    elif 240 <= book_num <= 266:
        return book_num - 200
    return book_num

def map_verse_id(verse_id):
    """Map assigned verse ID to standard format"""
    if not verse_id or len(verse_id) < 9:
        return verse_id
    try:
        book = int(verse_id[:3])
        chapter = int(verse_id[3:6])
        verse = int(verse_id[6:9])
        mapped_book = map_book(book)
        return f"{mapped_book:03d}{chapter:03d}{verse:03d}"
    except:
        return verse_id

def get_book_name(book_num):
    """Get Bible book name from number"""
    names = {
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
    return names.get(book_num, f"Book {book_num}")

class BookMappingConfig:
    pass
