"""
Language Survey Report - Telios schema only (survey, response, participant, person).
"""

import pandas as pd
from typing import Dict, Any

from reports.base_report_v2 import BaseReportV2


class LanguageSurveyReport(BaseReportV2):
    """Language survey analysis using registered Telios tables only."""

    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.survey_id = self._get_language_survey_id()

    def _get_language_survey_id(self) -> int:
        query = """
        SELECT id FROM survey 
        WHERE survey ILIKE '%language%' OR survey ILIKE '%lang%'
        LIMIT 1
        """
        try:
            df = self.schema_query(query, ["survey"])
            if not df.empty:
                return int(df['id'].iloc[0])
        except Exception:
            pass
        return None

    def generate(self) -> Dict[str, pd.DataFrame]:
        results = {
            'survey_overview': self._get_survey_overview(),
            'participant_summary': self._get_participant_summary(),
            'question_analysis': self._get_question_analysis(),
            'language_demographics': self._get_language_demographics(),
            'detailed_responses': self._get_detailed_responses(),
        }
        results['summary_stats'] = self._get_summary_stats(results)
        return results

    def _get_survey_overview(self) -> pd.DataFrame:
        if not self.survey_id:
            return self.schema_message('Language Survey not found')

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
        return self.schema_query(query, ["survey", "response"])

    def _get_participant_summary(self) -> pd.DataFrame:
        if not self.survey_id:
            return self.schema_message('Language Survey not found')

        query = f"""
        SELECT 
            COALESCE(p.firstname || ' ' || p.lastname, 'Unknown') as participant_name,
            r.role,
            COALESCE(c.country, p.country, p.presentaddresscountry) as country,
            r.unitid
        FROM response r
        LEFT JOIN participant pt ON r.participant = pt.id
        LEFT JOIN person p ON COALESCE(pt.person, r.participant) = p.id
        LEFT JOIN country c ON p.country_id = c.id
        WHERE r.survey = {self.survey_id}
        ORDER BY participant_name
        """
        return self.schema_query(
            query,
            ["response", "participant", "person", "country"],
        )

    def _get_question_analysis(self) -> pd.DataFrame:
        if not self.survey_id:
            return self.schema_message('Language Survey not found')

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
        return self.schema_query(
            query,
            ["question", "responseanswers", "response", "answeroption"],
        )

    def _get_language_demographics(self) -> pd.DataFrame:
        if not self.survey_id:
            return self.schema_message('Language Survey not found')

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
        return self.schema_query(
            query,
            ["question", "responseanswers", "answeroption"],
        )

    def _get_detailed_responses(self) -> pd.DataFrame:
        if not self.survey_id:
            return self.schema_message('Language Survey not found')

        query = f"""
        SELECT 
            COALESCE(p.firstname || ' ' || p.lastname, 'Unknown') as participant_name,
            r.role,
            r.batchid as batch_reference,
            q.text as question,
            q.questiontype,
            COALESCE(ao.optionvalue, '') as selected_option,
            COALESCE(ra.answertext, '') as free_text_answer
        FROM response r
        LEFT JOIN participant pt ON r.participant = pt.id
        LEFT JOIN person p ON COALESCE(pt.person, r.participant) = p.id
        LEFT JOIN responseanswers ra ON r.id = ra.response
        LEFT JOIN question q ON ra.question = q.id
        LEFT JOIN answeroption ao ON ra.answeroption = ao.id
        WHERE r.survey = {self.survey_id}
        ORDER BY participant_name, q.id
        """
        df = self.schema_query(
            query,
            ["response", "participant", "person", "responseanswers", "question", "answeroption"],
        )
        return df.fillna('')

    def _get_summary_stats(self, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        stats = []

        if 'survey_overview' in results and not results['survey_overview'].empty:
            row = results['survey_overview'].iloc[0]
            if 'Message' not in results['survey_overview'].columns:
                stats.append({'Metric': 'Survey Name', 'Value': row.get('survey_name', 'N/A')})
                stats.append({'Metric': 'Total Responses', 'Value': row.get('total_responses', 0)})
                stats.append({'Metric': 'Unique Respondents', 'Value': row.get('unique_respondents', 0)})
                stats.append({'Metric': 'Batches Represented', 'Value': row.get('batches_represented', 0)})

        if 'participant_summary' in results and not results['participant_summary'].empty:
            df = results['participant_summary']
            if 'Message' not in df.columns:
                stats.append({'Metric': 'Roles Represented', 'Value': df['role'].nunique() if 'role' in df.columns else 0})
                stats.append({'Metric': 'Countries', 'Value': df['country'].nunique() if 'country' in df.columns else 0})

        if not stats:
            stats = [{'Metric': 'Status', 'Value': 'No survey data available'}]

        return pd.DataFrame(stats)

