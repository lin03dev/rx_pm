#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
"""
Generate Language Survey Uploader Template
Matches the exact format for uploading language survey data
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def generate_language_uploader_template():
    """Generate template for uploading language survey responses"""
    
    output_dir = Path("./output/templates/Language")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "language_survey_uploader_template.xlsx"
    
    print("="*60)
    print("LANGUAGE SURVEY UPLOADER TEMPLATE GENERATOR")
    print("="*60)
    
    # Define the template structure matching your data format
    template_data = {
        'survey_id': ['43', '43', '43'],
        'survey_name': ['Language Background', 'Language Background', 'Language Background'],
        'survey_type': ['Language', 'Language', 'Language'],
        'question_id: question': [
            '573: What is the name of your language?',
            '574: Are there any alternative names of this language?',
            '575: Which people group speak this language?'
        ],
        'answeroption_id : answeroption': ['N/A', 'N/A', 'N/A'],
        'text (for free text type questions)': ['Halbi', 'Halvi', 'Halbi, Sunari']
    }
    
    df = pd.DataFrame(template_data)
    
    # Create instructions sheet
    instructions_df = pd.DataFrame({
        'Instruction': [
            'LANGUAGE SURVEY UPLOADER TEMPLATE',
            '=' * 50,
            '',
            'PURPOSE:',
            'Use this template to upload language survey responses to the system',
            '',
            'FORMAT (Matches your existing data collection format):',
            '- survey_id: The ID of the survey (43=Language Background, 44=Language Usage, etc.)',
            '- survey_name: Name of the survey',
            '- survey_type: Always "Language" for language surveys',
            '- question_id: question: The question ID followed by colon and the question text',
            '- answeroption_id : answeroption: The answer option ID and value (N/A for free text)',
            '- text (for free text type questions): The actual answer/text response',
            '',
            'IMPORTANT RULES:',
            '1. Each row represents ONE answer to ONE question',
            '2. For multiple choice questions, use answeroption_id:answeroption format',
            '3. For free text questions, leave answeroption_id as N/A and put text in last column',
            '4. All responses for a respondent should be grouped together',
            '5. Do not modify column headers',
            '',
            'SURVEY ID REFERENCE:',
            '- 43: Language Background',
            '- 44: Language Usage', 
            '- 45: Resources & Materials',
            '- 46: Community & Members',
            '- 47: Language Use, Attitude & Vitality (LUAV)',
            '- 48: Wordlist Collection',
            '',
            'EXAMPLE ROW:',
            '| 43 | Language Background | Language | 573: What is the name of your language? | N/A | Halbi |',
            '',
            'MULTIPLE CHOICE EXAMPLE:',
            '| 44 | Language Usage | Language | 589: Homes | 991: Yes | Yes |',
            '',
            'Contact: support@example.com for questions'
        ]
    })
    
    # Create example data for all survey types
    example_data = []
    
    # Example responses for Language Background (Survey 43)
    bg_questions = [
        (43, 'Language Background', '573: What is the name of your language?', 'N/A', 'Halbi'),
        (43, 'Language Background', '574: Are there any alternative names of this language?', 'N/A', 'Halvi'),
        (43, 'Language Background', '575: Which people group speak this language?', 'N/A', 'Halbi, Sunari'),
        (43, 'Language Background', '576: Where is this language primarily spoken?', 'N/A', 'Home, Market, Village Meeting'),
        (43, 'Language Background', '577: Country', 'N/A', 'India'),
        (43, 'Language Background', '578: State/Province', 'N/A', 'Odisha'),
        (43, 'Language Background', '579: District', 'N/A', 'Malkhanagiri'),
    ]
    
    # Example responses for Language Usage (Survey 44)
    usage_questions = [
        (44, 'Language Usage', '589: Homes', '991: Yes', 'Yes'),
        (44, 'Language Usage', '590: Market Place', '993: Yes', 'Yes'),
        (44, 'Language Usage', '591: Community Buildings', '995: Yes', 'Yes'),
    ]
    
    # Example responses for LUAV (Survey 47) - Multiple choice
    luav_questions = [
        (47, 'Language Use, Attitude & Vitality (LUAV)', '624: Can your children speak (Mother Tongue) as fluently as elder people?', '1021: No', 'No'),
        (47, 'Language Use, Attitude & Vitality (LUAV)', '625: How often do you use your mother tongue?', '1001: Everyday', 'Everyday'),
        (47, 'Language Use, Attitude & Vitality (LUAV)', '635: Speak your language?', '1012: Good', 'Good'),
    ]
    
    # Combine all examples
    for ex in bg_questions + usage_questions + luav_questions:
        example_data.append({
            'survey_id': ex[0],
            'survey_name': ex[1],
            'survey_type': 'Language',
            'question_id: question': ex[2],
            'answeroption_id : answeroption': ex[3],
            'text (for free text type questions)': ex[4]
        })
    
    example_df = pd.DataFrame(example_data)
    
    # Save to Excel with multiple sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
        df.to_excel(writer, sheet_name='Template_Structure', index=False)
        example_df.to_excel(writer, sheet_name='Example_Data', index=False)
        
        # Add a blank template sheet for users to fill
        blank_template = pd.DataFrame({
            'survey_id': [''],
            'survey_name': [''],
            'survey_type': ['Language'],
            'question_id: question': [''],
            'answeroption_id : answeroption': [''],
            'text (for free text type questions)': ['']
        })
        blank_template.to_excel(writer, sheet_name='Blank_Template', index=False)
    
    print(f"✅ Generated: {output_path.name}")
    print(f"   Location: {output_dir}")
    
    return output_path


def generate_wordlist_uploader_template():
    """Generate specialized template for wordlist collection"""
    
    output_dir = Path("./output/templates/Language")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "wordlist_uploader_template.xlsx"
    
    # Wordlist questions from your data (survey 48)
    wordlist_words = [
        (650, "Head – सिर", "Mud"),
        (651, "Hair – बाल", "Chundi, Bal"),
        (653, "Eye – आँख", "Aayek"),
        (654, "Ear – कान", "Kaan"),
        (655, "Nose – नाक", "Naak"),
        (656, "Leg – टाँग", "Jaang"),
        (657, "Heart – दिल", "Chati"),
        (658, "Village – गाँव", "Gaon"),
        (659, "House – घर", "Ghar"),
        (660, "Door – दरवाजा", "Kopaatt"),
    ]
    
    template_data = []
    for q_id, word, example in wordlist_words:
        template_data.append({
            'survey_id': 48,
            'survey_name': 'Wordlist Collection',
            'survey_type': 'Language',
            'question_id: question': f'{q_id}: {word}',
            'answeroption_id : answeroption': 'N/A',
            'text (for free text type questions)': example
        })
    
    df = pd.DataFrame(template_data)
    
    # Add blank rows for new entries
    blank_rows = pd.DataFrame({
        'survey_id': [48] * 20,
        'survey_name': ['Wordlist Collection'] * 20,
        'survey_type': ['Language'] * 20,
        'question_id: question': [''] * 20,
        'answeroption_id : answeroption': ['N/A'] * 20,
        'text (for free text type questions)': [''] * 20
    })
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Instructions sheet
        instructions = pd.DataFrame({
            'Instruction': [
                'WORDLIST COLLECTION UPLOADER TEMPLATE',
                '=' * 50,
                '',
                'PURPOSE:',
                'Use this template to upload wordlist/lexicon data',
                '',
                'INSTRUCTIONS:',
                '1. Each row represents one word translation',
                '2. Fill in the word in your language in the last column',
                '3. Use standard spelling as much as possible',
                '4. For multiple translations, separate with commas',
                '',
                'COLUMNS:',
                '- survey_id: Always 48 for Wordlist Collection',
                '- survey_name: Always "Wordlist Collection"',
                '- survey_type: Always "Language"',
                '- question_id: question: The word ID and English word',
                '- answeroption_id : answeroption: Always "N/A" for wordlist',
                '- text (for free text type questions): Your language translation'
            ]
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        # Example data
        df.to_excel(writer, sheet_name='Example_Data', index=False)
        
        # Blank template for user
        blank_rows.to_excel(writer, sheet_name='Blank_Template', index=False)
    
    print(f"✅ Generated: {output_path.name}")
    
    return output_path


def generate_complete_uploader_package():
    """Generate all uploader templates"""
    
    print("\n" + "="*60)
    print("GENERATING COMPLETE UPLOADER PACKAGE")
    print("="*60)
    
    # Main uploader template
    generate_language_uploader_template()
    
    # Wordlist specialized template
    generate_wordlist_uploader_template()
    
    # Create a data dictionary reference
    output_dir = Path("./output/templates/Language")
    
    reference_data = {
        'Survey ID': [43, 44, 45, 46, 47, 48],
        'Survey Name': [
            'Language Background',
            'Language Usage',
            'Resources & Materials',
            'Community & Members',
            'Language Use, Attitude & Vitality (LUAV)',
            'Wordlist Collection'
        ],
        'Description': [
            'Basic language information, name, location, speakers',
            'How and where the language is used',
            'Available resources and materials in the language',
            'Community members and leaders',
            'Language vitality, attitudes, and usage patterns',
            'Wordlist/lexicon collection'
        ]
    }
    
    reference_df = pd.DataFrame(reference_data)
    ref_path = output_dir / "survey_reference.xlsx"
    reference_df.to_excel(ref_path, index=False)
    print(f"✅ Generated: {ref_path.name}")
    
    print(f"\n📁 All templates saved in: {output_dir}")
    print("\n📋 Generated Files:")
    print("   1. language_survey_uploader_template.xlsx - Main uploader template")
    print("   2. wordlist_uploader_template.xlsx - Specialized wordlist template")
    print("   3. survey_reference.xlsx - Survey ID reference")


if __name__ == '__main__':
    generate_complete_uploader_package()
