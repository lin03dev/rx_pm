#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
"""
DYNAMIC Language Survey Template Generator
Generates templates directly from database schema
"""

import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager


def get_language_surveys(db_manager):
    """Get all language surveys from database"""
    query = """
    SELECT id, survey, survey_type 
    FROM survey 
    WHERE survey_type = 'Language' OR survey ILIKE '%language%'
    ORDER BY id
    """
    return db_manager.execute_query(query)


def get_survey_questions(db_manager, survey_id):
    """Get all questions for a survey in correct order"""
    query = f"""
    SELECT 
        q.id,
        q.text as question_text,
        q.questiontype,
        q.surveyorder
    FROM question q
    WHERE q.surveyid = {survey_id}
    ORDER BY q.surveyorder, q.id
    """
    return db_manager.execute_query(query)


def get_answer_options(db_manager, question_id):
    """Get answer options for a multiple choice question"""
    query = f"""
    SELECT optionvalue, sequence
    FROM answeroption
    WHERE question = {question_id}
    ORDER BY sequence
    """
    return db_manager.execute_query(query)


def generate_template_from_db(db_manager, output_dir):
    """Generate templates dynamically from database"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("DYNAMIC LANGUAGE SURVEY TEMPLATE GENERATOR")
    print("="*70)
    print("Reading from database...")
    
    # Get all language surveys
    surveys_df = get_language_surveys(db_manager)
    
    if surveys_df.empty:
        print("❌ No language surveys found in database")
        return
    
    print(f"\n📋 Found {len(surveys_df)} language surveys")
    
    all_templates = []
    
    # Generate individual templates for each survey
    for _, survey in surveys_df.iterrows():
        survey_id = survey['id']
        survey_name = survey['survey']
        
        print(f"\n📊 Processing: {survey_name} (ID: {survey_id})")
        
        # Get questions for this survey
        questions_df = get_survey_questions(db_manager, survey_id)
        
        if questions_df.empty:
            print(f"   ⚠️ No questions found")
            continue
        
        # Build template data from database
        template_data = []
        
        for _, q in questions_df.iterrows():
            question_id = q['id']
            question_text = q['question_text']
            question_type = q['questiontype']
            
            # For multiple choice questions, get options
            answer_option_value = "N/A"
            if question_type in [1, 2, 4, 5]:  # Multiple choice types
                options_df = get_answer_options(db_manager, question_id)
                if not options_df.empty:
                    # Format as "id: option" for multiple choice
                    options_list = [f"{opt['sequence']}: {opt['optionvalue']}" 
                                   for _, opt in options_df.iterrows()]
                    answer_option_value = f"Select from: {', '.join(options_list)}"
            
            template_data.append({
                'survey_id': survey_id,
                'survey_name': survey_name,
                'survey_type': 'Language',
                'questionid: question': f"{question_id}: {question_text}",
                'answeroptionid : answeroption': answer_option_value,
                'text (for free text type questions)': ''
            })
        
        # Create DataFrame
        df = pd.DataFrame(template_data)
        
        # Save individual template
        safe_name = survey_name.lower().replace(' ', '_').replace('&', 'and').replace(',', '')
        safe_name = re.sub(r'[^\w\-_]', '_', safe_name)
        output_path = output_dir / f"{safe_name}_template.xlsx"
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Instructions sheet
            instructions = pd.DataFrame({
                'Instruction': [
                    f'SURVEY: {survey_name}',
                    '=' * 50,
                    '',
                    f'Total Questions: {len(questions_df)}',
                    '',
                    'INSTRUCTIONS:',
                    '1. Add a "respondent_id" column at the beginning',
                    '2. Fill one row per question per respondent',
                    '3. For multiple choice, use the provided options',
                    '4. For text questions, put answer in last column',
                    '5. Do not modify column headers'
                ]
            })
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
            
            # Template data
            df.to_excel(writer, sheet_name='Survey_Data', index=False)
            
            # Blank template for users
            blank_df = pd.DataFrame({
                'survey_id': [''],
                'survey_name': [''],
                'survey_type': ['Language'],
                'questionid: question': [''],
                'answeroptionid : answeroption': [''],
                'text (for free text type questions)': ['']
            })
            blank_df.to_excel(writer, sheet_name='Blank_Template', index=False)
        
        print(f"   ✅ Generated: {output_path.name}")
        all_templates.append(output_path)
    
    # Generate master template (all surveys combined)
    print(f"\n📊 Generating Master Template...")
    
    master_path = output_dir / "language_survey_master_template.xlsx"
    with pd.ExcelWriter(master_path, engine='openpyxl') as writer:
        # Instructions
        instructions = pd.DataFrame({
            'Instruction': [
                'LANGUAGE SURVEY MASTER TEMPLATE',
                '=' * 50,
                '',
                'This template combines all language surveys',
                'Each sheet represents a different survey',
                '',
                'HOW TO USE:',
                '1. Add a "respondent_id" column to each sheet',
                '2. Fill responses for each survey separately',
                '3. Save and upload each sheet',
                '',
                f'Total Surveys: {len(surveys_df)}'
            ]
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        # Create a sheet for each survey
        for _, survey in surveys_df.iterrows():
            survey_id = survey['id']
            survey_name = survey['survey']
            
            questions_df = get_survey_questions(db_manager, survey_id)
            if questions_df.empty:
                continue
            
            sheet_data = []
            for _, q in questions_df.iterrows():
                sheet_data.append({
                    'respondent_id': '',
                    'respondent_name': '',
                    'email': '',
                    'batch_name': '',
                    'question_id': q['id'],
                    'question': q['question_text'],
                    'answer_option': '',
                    'text_answer': ''
                })
            
            df = pd.DataFrame(sheet_data)
            sheet_name = survey_name[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"   ✅ Generated: {master_path.name}")
    all_templates.append(master_path)
    
    # Generate uploader template (for batch import)
    print(f"\n📊 Generating Uploader Template...")
    
    uploader_path = output_dir / "language_survey_uploader_template.xlsx"
    
    # Build complete question list for uploader
    uploader_data = []
    for _, survey in surveys_df.iterrows():
        survey_id = survey['id']
        survey_name = survey['survey']
        questions_df = get_survey_questions(db_manager, survey_id)
        
        for _, q in questions_df.iterrows():
            uploader_data.append({
                'respondent_id': '',
                'participant_name': '',
                'email': '',
                'batch_name': '',
                'survey_id': survey_id,
                'survey_name': survey_name,
                'survey_type': 'Language',
                'questionid: question': f"{q['id']}: {q['question_text']}",
                'answeroptionid : answeroption': '',
                'text (for free text type questions)': ''
            })
    
    uploader_df = pd.DataFrame(uploader_data)
    
    with pd.ExcelWriter(uploader_path, engine='openpyxl') as writer:
        # Instructions
        instructions = pd.DataFrame({
            'Instruction': [
                'LANGUAGE SURVEY UPLOADER TEMPLATE',
                '=' * 50,
                '',
                'This template is ready for data upload',
                '',
                'COLUMN DESCRIPTIONS:',
                '- respondent_id: Unique identifier for each respondent',
                '- participant_name: Name of the respondent',
                '- email: Email address',
                '- batch_name: Batch identifier',
                '- survey_id: Survey ID (from database)',
                '- survey_name: Survey name',
                '- survey_type: Always "Language"',
                '- questionid: question: Format "ID: Question text"',
                '- answeroptionid : answeroption: For multiple choice, use "ID: Option"',
                '- text: For free text questions, put answer here',
                '',
                'IMPORTANT:',
                '1. Fill one row per question per respondent',
                '2. Do not modify column headers',
                '3. Save as CSV or Excel for upload'
            ]
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
        uploader_df.to_excel(writer, sheet_name='Upload_Data', index=False)
        
        # Add example row
        example_data = uploader_data[:5]  # First 5 questions as example
        for row in example_data:
            row['respondent_id'] = 'R001'
            row['participant_name'] = 'John Doe'
            row['email'] = 'john@example.com'
            row['batch_name'] = 'BATCH_001'
        example_df = pd.DataFrame(example_data)
        example_df.to_excel(writer, sheet_name='Example_Data', index=False)
    
    print(f"   ✅ Generated: {uploader_path.name}")
    all_templates.append(uploader_path)
    
    # Save survey reference
    ref_path = output_dir / "survey_reference.xlsx"
    surveys_df.to_excel(ref_path, index=False)
    print(f"   ✅ Generated: {ref_path.name}")
    
    print(f"\n📁 All templates saved in: {output_dir}")
    print(f"   Total templates: {len(all_templates)}")
    
    return all_templates


if __name__ == '__main__':
    import re
    db_config = DatabaseConfigManager()
    db_manager = DatabaseManager(db_config)
    db_manager.current_db = 'Telios_LMS_Dev'
    
    generate_template_from_db(db_manager, Path("./output/templates/Language"))
