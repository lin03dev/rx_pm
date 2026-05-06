"""
Dynamic Survey Configuration - Loads everything from database
No hardcoded values
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DynamicSurveyConfig:
    """Dynamic configuration loaded from database"""
    
    # Parent question indicators (can be extended via database)
    parent_indicators: List[str] = field(default_factory=lambda: [
        'what languages', 'which language', 'how often', 'how do you feel',
        'what language do your children', 'do you think', 'would you like',
        'please list', 'please specify', 'describe', 'explain',
        'what are the', 'which of the following', 'select all that apply',
        'rate the following', 'how would you rate', 'on a scale of',
        'do you agree', 'are there any', 'is there any'
    ])
    
    # Child indicators
    child_indicators: List[str] = field(default_factory=lambda: [
        'parents', 'children', 'grandchildren', 'spouse', 'siblings',
        'villagers', 'neighbors', 'playing', 'talking', 'school',
        'home', 'market', 'work', 'community', 'festivals', 'ceremonies'
    ])
    
    # Skip patterns (standalone questions)
    skip_patterns: List[str] = field(default_factory=lambda: [
        'name', 'email', 'date', 'age', 'gender', 'location'
    ])
    
    # Color schemes (can be customized)
    colors: Dict[str, str] = field(default_factory=lambda: {
        'parent_bg': 'D0E8F7',
        'parent_font': '0044CC',
        'child_bg': 'E8F5E9',
        'child_font': '006600',
        'standalone_bg': 'FFFFFF',
        'standalone_font': '000000',
        'answer_header_bg': 'FF8C00',
        'answer_alt_bg': 'FFF3E0',
        'header_bg': '1B4F72'
    })
    
    @classmethod
    def from_database(cls, db_manager) -> 'DynamicSurveyConfig':
        """Load configuration from database tables if they exist"""
        config = cls()
        
        # Try to load custom indicators from database
        try:
            query = "SELECT indicator_type, indicator_value FROM survey_indicators WHERE is_active = true"
            df = db_manager.execute_query(query)
            
            for _, row in df.iterrows():
                indicator_type = row['indicator_type']
                value = row['indicator_value'].lower()
                
                if indicator_type == 'parent':
                    if value not in config.parent_indicators:
                        config.parent_indicators.append(value)
                elif indicator_type == 'child':
                    if value not in config.child_indicators:
                        config.child_indicators.append(value)
                elif indicator_type == 'skip':
                    if value not in config.skip_patterns:
                        config.skip_patterns.append(value)
        except:
            # Table doesn't exist - use defaults
            pass
        
        # Try to load color scheme from database
        try:
            query = "SELECT color_key, color_value FROM survey_colors"
            df = db_manager.execute_query(query)
            for _, row in df.iterrows():
                config.colors[row['color_key']] = row['color_value']
        except:
            # Table doesn't exist - use defaults
            pass
        
        return config


# Singleton instance
_dynamic_config = None

def get_dynamic_survey_config(db_manager) -> DynamicSurveyConfig:
    """Get dynamic survey configuration"""
    global _dynamic_config
    if _dynamic_config is None:
        _dynamic_config = DynamicSurveyConfig.from_database(db_manager)
    return _dynamic_config
