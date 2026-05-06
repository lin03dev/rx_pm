#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
"""
Generate Excel templates with segregated output directories
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.excel_template_generator import get_excel_template_generator


def main():
    print("=" * 60)
    print("EXCEL TEMPLATE GENERATOR")
    print("=" * 60)
    
    generator = get_excel_template_generator()
    
    # Generate templates to different directories based on purpose
    template_categories = {
        'user_import': 'AG',
        'project_import': 'AG',
        'assignment_import': 'AG',
        'worklog_import': 'AG',
        'bible_chapter_import': 'AG',
        'obs_chapter_import': 'AG',
        'literature_genre_import': 'AG',
        'grammar_import': 'AG',
        'batch_creation': 'LMS',
        'student_enrollment': 'LMS',
        'batch_module': 'LMS',
        'attendance': 'LMS',
        'assignment_submission': 'LMS',
        'survey_response': 'Telios',
    }
    
    generated = []
    
    for template_name, category in template_categories.items():
        try:
            # Override output directory for this template
            generator.output_dir = Path(f"./output/templates/{category}")
            generator.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Find and generate the template
            from config.excel_template_config import TemplatePurpose, get_excel_template_manager
            
            manager = get_excel_template_manager()
            for purpose in TemplatePurpose:
                template = manager.get_template(purpose)
                if template and template.name == template_name:
                    file_path = generator.generate_template(purpose)
                    generated.append((file_path, category))
                    print(f"✅ Generated: {file_path.name} → output/templates/{category}/")
                    break
        except Exception as e:
            print(f"❌ Failed to generate {template_name}: {e}")
    
    print(f"\n✅ Generated {len(generated)} templates")
    print("\n📁 Template locations:")
    print("   • AG templates → output/templates/AG/")
    print("   • LMS templates → output/templates/LMS/")
    print("   • Telios templates → output/templates/Telios/")
    print("   • Language templates → output/templates/Language/")


if __name__ == '__main__':
    main()
