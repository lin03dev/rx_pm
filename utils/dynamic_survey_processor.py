"""
Dynamic Survey Processor - No hardcoded values, all dynamic
Handles missing tables gracefully
"""

import re
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple


class DynamicSurveyProcessor:
    """Process surveys dynamically with configurable patterns"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._load_config()
    
    def _load_config(self):
        """Load configuration with fallbacks for missing tables"""
        # Default parent indicators
        self.parent_indicators = [
            'what languages', 'which language', 'how often', 'how do you feel',
            'what language do your children', 'do you think', 'would you like',
            'please list', 'please specify', 'describe', 'explain',
            'what are the', 'which of the following', 'select all that apply',
            'rate the following', 'how would you rate', 'on a scale of',
            'do you agree', 'are there any', 'is there any'
        ]
        
        # Default child indicators
        self.child_indicators = [
            'parents', 'children', 'grandchildren', 'spouse', 'siblings',
            'villagers', 'neighbors', 'playing', 'talking', 'school',
            'home', 'market', 'work', 'community', 'festivals', 'ceremonies'
        ]
        
        # Default skip patterns
        self.skip_patterns = [
            'name', 'email', 'date', 'age', 'gender', 'location'
        ]
        
        # Default colors
        self.colors = {
            'parent_bg': 'D0E8F7',
            'parent_font': '0044CC',
            'child_bg': 'E8F5E9',
            'child_font': '006600',
            'standalone_bg': 'FFFFFF',
            'standalone_font': '000000',
            'answer_header_bg': 'FF8C00',
            'answer_alt_bg': 'FFF3E0',
            'header_bg': '1B4F72'
        }
        
        # Try to load from database if tables exist (fail gracefully)
        try:
            # Reset connection first to clear any transaction issues
            self.db_manager.reset_connection()
            
            # Check if table exists before querying
            if self.db_manager.table_exists('survey_indicators'):
                query = "SELECT indicator_type, indicator_value FROM survey_indicators WHERE is_active = true"
                df = self.db_manager.execute_query(query)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        indicator_type = row['indicator_type']
                        value = row['indicator_value'].lower()
                        if indicator_type == 'parent' and value not in self.parent_indicators:
                            self.parent_indicators.append(value)
                        elif indicator_type == 'child' and value not in self.child_indicators:
                            self.child_indicators.append(value)
                        elif indicator_type == 'skip' and value not in self.skip_patterns:
                            self.skip_patterns.append(value)
        except Exception as e:
            pass  # Table doesn't exist or error, use defaults
        
        try:
            if self.db_manager.table_exists('survey_colors'):
                query = "SELECT color_key, color_value FROM survey_colors"
                df = self.db_manager.execute_query(query)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        self.colors[row['color_key']] = row['color_value']
        except Exception as e:
            pass  # Table doesn't exist, use defaults
    
    def reset(self):
        """Reset the processor and reload config"""
        self._load_config()
    
    def get_surveys(self):
        """Get all surveys dynamically"""
        query = """
        SELECT id, survey, survey_type
        FROM survey 
        ORDER BY id
        """
        df = self.db_manager.execute_query(query)
        return df if df is not None else pd.DataFrame()
    
    def get_survey_questions(self, survey_id: int):
        """Get questions for a survey dynamically"""
        query = f"""
        SELECT 
            q.id as question_id,
            q.text as question_text,
            q.questiontype,
            q.surveyorder
        FROM question q
        WHERE q.surveyid = {survey_id}
        ORDER BY q.surveyorder, q.id
        """
        df = self.db_manager.execute_query(query)
        return df if df is not None else pd.DataFrame()
    
    def get_answer_options(self, question_id: int):
        """Get answer options dynamically"""
        query = f"""
        SELECT id, optionvalue, sequence
        FROM answeroption
        WHERE question = {question_id}
        ORDER BY sequence
        """
        df = self.db_manager.execute_query(query)
        return df if df is not None else pd.DataFrame()
    
    def detect_parent_child(self, questions_df):
        """Dynamically detect parent-child relationships"""
        relationships = []
        current_parent = None
        
        if questions_df is None or questions_df.empty:
            return relationships
        
        for idx, row in questions_df.iterrows():
            q_id = row['question_id']
            q_text = row['question_text'].lower()
            q_type = row['questiontype']
            
            is_parent = self._is_parent_question(q_text)
            is_skip = self._is_skip_question(q_text)
            
            if is_parent and not is_skip:
                current_parent = {
                    'id': q_id,
                    'text': row['question_text'],
                    'type': q_type
                }
                relationships.append({
                    'question_id': q_id,
                    'question_text': row['question_text'],
                    'question_type': q_type,
                    'parent_id': None,
                    'level': 0,
                    'is_parent': True
                })
            else:
                is_child = self._is_child_question(q_text, current_parent['text'].lower() if current_parent else '')
                relationships.append({
                    'question_id': q_id,
                    'question_text': row['question_text'],
                    'question_type': q_type,
                    'parent_id': current_parent['id'] if current_parent and is_child else None,
                    'level': 1 if current_parent and is_child else 0,
                    'is_parent': False
                })
        
        return relationships
    
    def _is_parent_question(self, text: str) -> bool:
        """Dynamic parent detection"""
        return any(indicator in text for indicator in self.parent_indicators) or len(text) > 40
    
    def _is_child_question(self, child_text: str, parent_text: str) -> bool:
        """Dynamic child detection"""
        if not parent_text:
            return False
        
        parent_keywords = re.findall(r'\b\w+\b', parent_text)
        for keyword in parent_keywords:
            if len(keyword) > 3 and keyword in child_text:
                return True
        
        return any(indicator in child_text for indicator in self.child_indicators)
    
    def _is_skip_question(self, text: str) -> bool:
        """Check if question should be standalone"""
        return any(pattern in text for pattern in self.skip_patterns)
    
    def get_survey_structure(self, survey_id: int) -> Dict[str, Any]:
        """Get complete survey structure dynamically"""
        questions_df = self.get_survey_questions(survey_id)
        relationships = self.detect_parent_child(questions_df)
        
        return {
            'survey_id': survey_id,
            'total_questions': len(questions_df),
            'parents': [r for r in relationships if r.get('is_parent')],
            'children': [r for r in relationships if r.get('parent_id')],
            'standalone': [r for r in relationships if not r.get('is_parent') and not r.get('parent_id')],
            'relationships': relationships
        }
    
    def get_display_config(self) -> Dict[str, str]:
        """Get display configuration dynamically"""
        return self.colors
