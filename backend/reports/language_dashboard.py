"""
Language Dashboard - Consolidated view of all language surveys
"""

import pandas as pd
from typing import Dict, Any

from reports.base_report_v2 import BaseReportV2


class LanguageDashboard(BaseReportV2):
    """
    Consolidated Language Dashboard
    Combines all language surveys into one comprehensive view
    """
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate language dashboard"""
        
        results = {}
        
        # 1. All Language Surveys Summary
        results['surveys_summary'] = self._get_surveys_summary()
        
        # 2. Language Background Summary
        results['background_summary'] = self._get_background_summary()
        
        # 3. Language Usage Summary
        results['usage_summary'] = self._get_usage_summary()
        
        # 4. Language Vitality Summary
        results['vitality_summary'] = self._get_vitality_summary()
        
        # 5. Key Insights
        results['key_insights'] = self._get_key_insights(results)
        
        return results
    
    def _get_surveys_summary(self) -> pd.DataFrame:
        """Get summary of all language surveys"""
        query = """
        SELECT 
            s.id,
            s.survey as survey_name,
            s.survey_type,
            COUNT(DISTINCT r.id) as total_responses,
            COUNT(DISTINCT r.participant) as respondents,
            COUNT(DISTINCT r.batchid) as batches
        FROM survey s
        LEFT JOIN response r ON s.id = r.survey
        WHERE s.survey_type = 'Language'
        GROUP BY s.id, s.survey, s.survey_type
        ORDER BY total_responses DESC
        """
        df = self.execute_query(query)
        return df
    
    def _get_background_summary(self) -> pd.DataFrame:
        """Get language background summary - fixed GROUP BY"""
        query = """
        SELECT 
            COALESCE(ra.answertext, ao.optionvalue, 'No response') as language,
            COUNT(*) as count
        FROM response r
        JOIN question q ON q.surveyid = r.survey
        JOIN responseanswers ra ON r.id = ra.response AND ra.question = q.id
        LEFT JOIN answeroption ao ON ra.answeroption = ao.id
        WHERE q.text ILIKE '%mother%' OR q.text ILIKE '%first language%' OR q.text ILIKE '%native%'
        GROUP BY COALESCE(ra.answertext, ao.optionvalue, 'No response')
        ORDER BY count DESC
        LIMIT 20
        """
        df = self.execute_query(query)
        return df
    
    def _get_usage_summary(self) -> pd.DataFrame:
        """Get language usage summary - fixed GROUP BY"""
        query = """
        SELECT 
            COALESCE(ra.answertext, ao.optionvalue, 'No response') as usage_context,
            COUNT(*) as count
        FROM response r
        JOIN question q ON q.surveyid = r.survey
        JOIN responseanswers ra ON r.id = ra.response AND ra.question = q.id
        LEFT JOIN answeroption ao ON ra.answeroption = ao.id
        WHERE q.text ILIKE '%use%' OR q.text ILIKE '%speak%'
        GROUP BY COALESCE(ra.answertext, ao.optionvalue, 'No response')
        ORDER BY count DESC
        LIMIT 20
        """
        df = self.execute_query(query)
        return df
    
    def _get_vitality_summary(self) -> pd.DataFrame:
        """Get language vitality summary - fixed GROUP BY"""
        query = """
        SELECT 
            COALESCE(ra.answertext, ao.optionvalue, 'No response') as vitality_indicator,
            COUNT(*) as count
        FROM response r
        JOIN question q ON q.surveyid = r.survey
        JOIN responseanswers ra ON r.id = ra.response AND ra.question = q.id
        LEFT JOIN answeroption ao ON ra.answeroption = ao.id
        WHERE q.text ILIKE '%vital%' OR q.text ILIKE '%attitude%' OR q.text ILIKE '%endanger%'
        GROUP BY COALESCE(ra.answertext, ao.optionvalue, 'No response')
        ORDER BY count DESC
        LIMIT 20
        """
        df = self.execute_query(query)
        return df
    
    def _get_key_insights(self, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Generate key insights from all data"""
        insights = []
        
        if 'surveys_summary' in results and not results['surveys_summary'].empty:
            df = results['surveys_summary']
            total_surveys = len(df)
            total_responses = df['total_responses'].sum() if 'total_responses' in df.columns else 0
            insights.append({'Insight': 'Total Language Surveys', 'Value': total_surveys})
            insights.append({'Insight': 'Total Survey Responses', 'Value': total_responses})
        
        if 'background_summary' in results and not results['background_summary'].empty:
            df = results['background_summary']
            if not df.empty and 'language' in df.columns:
                top_languages = df.head(3)['language'].tolist()
                insights.append({'Insight': 'Most Common Mother Tongues', 'Value': ', '.join(str(l) for l in top_languages if str(l) != 'No response')})
        
        return pd.DataFrame(insights)
    
