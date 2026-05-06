"""
Language Survey Report - Comprehensive analysis of language survey responses
"""

import pandas as pd
import re
from datetime import datetime
from typing import Dict, Any

from reports.base_report_v2 import BaseReportV2


class LanguageSurveyReport(BaseReportV2):
    """
    Comprehensive Language Survey Report
    Tracks survey responses about language needs, resources, and demographics
    """
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['batch_id', 'language', 'country']
        self.survey_id = self._get_language_survey_id()
    
    def _get_language_survey_id(self) -> int:
        """Get the Language Survey ID from the database"""
        query = """
        SELECT id FROM survey 
        WHERE survey ILIKE '%language%' OR survey ILIKE '%lang%'
        LIMIT 1
        """
        try:
            df = self.execute_query(query)
            if not df.empty:
                return df['id'].iloc[0]
        except:
            pass
        return None
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate Language Survey report"""
        
        results = {}
        
        # 1. Survey Overview
        results['survey_overview'] = self._get_survey_overview()
        
        # 2. Participant Responses Summary
        results['participant_summary'] = self._get_participant_summary()
        
        # 3. Question-wise Analysis
        results['question_analysis'] = self._get_question_analysis()
        
        # 4. Language Demographics
        results['language_demographics'] = self._get_language_demographics()
        
        # 5. Detailed Responses
        results['detailed_responses'] = self._get_detailed_responses()
        
        # 6. Summary Statistics
        results['summary_stats'] = self._get_summary_stats(results)
        
        return results
    
    def _get_survey_overview(self) -> pd.DataFrame:
        """Get survey overview information"""
        if not self.survey_id:
            return pd.DataFrame({'Message': ['Language Survey not found']})
        
        query = f"""
        SELECT 
            s.survey as survey_name,
            s.survey_type,
            COUNT(DISTINCT r.id) as total_responses,
            COUNT(DISTINCT r.participant) as unique_respondents,
            COUNT(DISTINCT r.batchid) as batches_represented
        FROM survey s
        LEFT JOIN response r ON s.id = r.survey
        WHERE s.id = {self.survey_id}
        GROUP BY s.survey, s.survey_type
        """
        df = self.execute_query(query)
        return df
    
    def _get_participant_summary(self) -> pd.DataFrame:
        """Get participant summary for the survey"""
        if not self.survey_id:
            return pd.DataFrame({'Message': ['Language Survey not found']})
        
        query = f"""
        SELECT 
            COALESCE(p.firstname || ' ' || p.lastname, 'Unknown') as participant_name,
            r.role,
            b.batch as batch_name,
            b.location,
            cnt.country as country
        FROM response r
        LEFT JOIN person p ON r.participant = p.id
        LEFT JOIN batch b ON r.batchid = b.id
        LEFT JOIN country cnt ON b.country = cnt.id
        WHERE r.survey = {self.survey_id}
        ORDER BY participant_name
        """
        df = self.execute_query(query)
        return df
    
    def _get_question_analysis(self) -> pd.DataFrame:
        """Get question-wise analysis of responses"""
        if not self.survey_id:
            return pd.DataFrame({'Message': ['Language Survey not found']})
        
        query = f"""
        SELECT 
            q.text as question,
            q.questiontype,
            COUNT(DISTINCT ra.id) as response_count,
            COUNT(DISTINCT r.participant) as respondent_count,
            COALESCE(ao.optionvalue, ra.answertext, 'No response') as answer,
            COUNT(ra.id) as answer_count
        FROM question q
        LEFT JOIN responseanswers ra ON q.id = ra.question
        LEFT JOIN response r ON ra.response = r.id
        LEFT JOIN answeroption ao ON ra.answeroption = ao.id
        WHERE q.surveyid = {self.survey_id}
        GROUP BY q.text, q.questiontype, ao.optionvalue, ra.answertext
        ORDER BY q.text, answer_count DESC
        """
        df = self.execute_query(query)
        return df
    
    def _get_language_demographics(self) -> pd.DataFrame:
        """Get language demographics from the survey"""
        if not self.survey_id:
            return pd.DataFrame({'Message': ['Language Survey not found']})
        
        # Look for language-related questions
        query = f"""
        SELECT 
            q.text as question,
            COALESCE(ra.answertext, ao.optionvalue, 'No response') as response,
            COUNT(*) as count
        FROM question q
        LEFT JOIN responseanswers ra ON q.id = ra.question
        LEFT JOIN answeroption ao ON ra.answeroption = ao.id
        WHERE q.surveyid = {self.survey_id}
          AND (q.text ILIKE '%language%' OR q.text ILIKE '%speak%' OR q.text ILIKE '%dialect%' 
               OR q.text ILIKE '%mother%' OR q.text ILIKE '%tongue%')
        GROUP BY q.text, ra.answertext, ao.optionvalue
        ORDER BY q.text, count DESC
        """
        df = self.execute_query(query)
        return df
    
    def _get_detailed_responses(self) -> pd.DataFrame:
        """Get detailed responses for all questions"""
        if not self.survey_id:
            return pd.DataFrame({'Message': ['Language Survey not found']})
        
        query = f"""
        SELECT 
            COALESCE(p.firstname || ' ' || p.lastname, 'Unknown') as participant_name,
            r.role,
            b.batch as batch_name,
            q.text as question,
            q.questiontype,
            COALESCE(ao.optionvalue, '') as selected_option,
            COALESCE(ra.answertext, '') as free_text_answer
        FROM response r
        LEFT JOIN person p ON r.participant = p.id
        LEFT JOIN batch b ON r.batchid = b.id
        LEFT JOIN responseanswers ra ON r.id = ra.response
        LEFT JOIN question q ON ra.question = q.id
        LEFT JOIN answeroption ao ON ra.answeroption = ao.id
        WHERE r.survey = {self.survey_id}
        ORDER BY participant_name, q.id
        """
        df = self.execute_query(query)
        df = df.fillna('')
        return df
    
    def _get_summary_stats(self, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Generate summary statistics"""
        stats = []
        
        if 'survey_overview' in results and not results['survey_overview'].empty:
            row = results['survey_overview'].iloc[0]
            stats.append({'Metric': 'Survey Name', 'Value': row.get('survey_name', 'N/A')})
            stats.append({'Metric': 'Total Responses', 'Value': row.get('total_responses', 0)})
            stats.append({'Metric': 'Unique Respondents', 'Value': row.get('unique_respondents', 0)})
            stats.append({'Metric': 'Batches Represented', 'Value': row.get('batches_represented', 0)})
        
        if 'participant_summary' in results and not results['participant_summary'].empty:
            df = results['participant_summary']
            stats.append({'Metric': 'Roles Represented', 'Value': df['role'].nunique() if 'role' in df.columns else 0})
            stats.append({'Metric': 'Countries', 'Value': df['country'].nunique() if 'country' in df.columns else 0})
        
        if 'question_analysis' in results and not results['question_analysis'].empty:
            df = results['question_analysis']
            stats.append({'Metric': 'Total Questions', 'Value': df['question'].nunique() if 'question' in df.columns else 0})
        
        if not stats:
            stats = [{'Metric': 'Status', 'Value': 'No data available'}]
        
        return pd.DataFrame(stats)
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'survey_overview': '1. Survey Overview',
            'participant_summary': '2. Participant Summary',
            'question_analysis': '3. Question-wise Analysis',
            'language_demographics': '4. Language Demographics',
            'detailed_responses': '5. Detailed Responses',
            'summary_stats': '6. Summary Statistics'
        }
