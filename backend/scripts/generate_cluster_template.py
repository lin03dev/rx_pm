#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
"""
Generate Language Cluster Mapping Template
"""

import pandas as pd
from pathlib import Path

output_dir = Path("./output/templates/Language")
output_dir.mkdir(parents=True, exist_ok=True)

print("="*60)
print("LANGUAGE CLUSTER TEMPLATE GENERATOR")
print("="*60)

# Create cluster mapping template
cluster_data = {
    'Language Name': ['', '', '', '', ''],
    'ISO Code': ['', '', '', '', ''],
    'Cluster Name': ['', '', '', '', ''],
    'Region': ['', '', '', '', ''],
    'Country': ['', '', '', '', ''],
    'Estimated Speakers': ['', '', '', '', ''],
    'Script': ['', '', '', '', ''],
    'Translation Status': ['Not Started', 'In Progress', 'Completed', 'Needs Review', ''],
    'Priority Level': ['High', 'Medium', 'Low', '', ''],
    'Notes': ['', '', '', '', '']
}

df = pd.DataFrame(cluster_data)

# Add example row as comment
output_path = output_dir / "language_cluster_template.xlsx"

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Language_Clusters', index=False)
    
    # Add instructions sheet
    instructions = pd.DataFrame({
        'Instruction': [
            'LANGUAGE CLUSTER MAPPING TEMPLATE',
            '=' * 50,
            '',
            'PURPOSE:',
            'This template helps organize languages into clusters for better reporting',
            '',
            'INSTRUCTIONS:',
            '1. Enter language information in each row',
            '2. Group related languages under the same cluster',
            '3. Provide accurate speaker estimates',
            '4. Update translation status regularly',
            '',
            'COLUMN DESCRIPTIONS:',
            '- Language Name: Official name of the language',
            '- ISO Code: 3-letter ISO 639-3 code',
            '- Cluster Name: Language family/cluster (e.g., Indo-Aryan, Dravidian)',
            '- Region: Geographic region (e.g., North India, South India)',
            '- Country: Primary country where language is spoken',
            '- Estimated Speakers: Approximate number of speakers',
            '- Script: Writing system used',
            '- Translation Status: Not Started, In Progress, Completed, Needs Review',
            '- Priority Level: High, Medium, Low',
            '- Notes: Any additional information',
            '',
            'EXAMPLE:',
            '- Language Name: Hindi',
            '- ISO Code: hin',
            '- Cluster Name: Indo-Aryan',
            '- Region: North India',
            '- Country: India',
            '- Estimated Speakers: 600,000,000',
            '- Script: Devanagari',
            '- Translation Status: In Progress',
            '- Priority Level: High'
        ]
    })
    instructions.to_excel(writer, sheet_name='Instructions', index=False)

print(f"✅ Generated: {output_path.name}")
print(f"📁 Location: {output_dir}")
