"""
OBS Mapping Config - Backward compatibility layer that uses dynamic config
"""

from config.dynamic_config import get_dynamic_config

def get_obs_mapping_config():
    return get_dynamic_config().get_obs_config()

def parse_obs_assigned_chapters(chapters_string):
    """Parse assigned OBS chapters"""
    result = set()
    if not chapters_string:
        return result
    for ch in chapters_string.split(','):
        ch = ch.strip()
        if ch and ch.isdigit():
            result.add(int(ch))
    return result

def get_obs_chapter_name(chapter_no):
    """Get OBS chapter name"""
    config = get_dynamic_config()
    names = config.get_obs_config().get('chapter_names', {})
    return names.get(str(chapter_no), f"Chapter {chapter_no}")

def get_obs_chapter_paragraph_count(chapter_no):
    """Get paragraph count for OBS chapter"""
    config = get_dynamic_config()
    counts = config.get_obs_config().get('chapter_paragraphs', {})
    return counts.get(str(chapter_no), 0)

def get_obs_audio_config():
    """Get OBS audio configuration"""
    config = get_dynamic_config()
    return config.get_obs_config().get('completion_thresholds', {'translation': 100, 'audio': 100})

def get_obs_mtt_config():
    """Get OBS MTT configuration"""
    return {
        'status_rules': {
            'completed': {'min_completion': 100, 'label': 'Completed'},
            'in_progress': {'min_completion': 1, 'max_completion': 99, 'label': 'In Progress'},
            'not_started': {'min_completion': 0, 'label': 'Not Started'}
        }
    }

class OBSMappingConfig:
    pass
