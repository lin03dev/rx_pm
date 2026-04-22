#!/usr/bin/env python3
"""
generate_templates.py - Generate all Excel templates
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
    files = generator.generate_all_templates()
    
    print("\n" + "=" * 60)
    print("TEMPLATES GENERATED:")
    print("=" * 60)
    
    for file_path in files:
        size = file_path.stat().st_size
        print(f"  ✅ {file_path.name} ({size:,} bytes)")
    
    print(f"\n📁 Location: {generator.output_dir.absolute()}")
    print("=" * 60)


if __name__ == '__main__':
    main()