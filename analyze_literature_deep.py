#!/usr/bin/env python3
"""
Deep analysis of literature content to understand the structure
"""

import sys
import json
sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager

db_config = DatabaseConfigManager()
db_manager = DatabaseManager(db_config)
db_manager.current_db = 'AG_Dev'

print("="*80)
print("LITERATURE CONTENT DEEP ANALYSIS")
print("="*80)

# Get detailed content for Ginuman_Lit.
query = """
SELECT 
    p.name as project_name,
    l.name as language_name,
    c.name as country,
    lg."genreId" as genre_type,
    lg.name as genre_name,
    lpg.version,
    lpg.content
FROM literature_project_genres_history lpg
JOIN literature_project_genres lg ON lpg."literatureProjectGenreId" = lg.id
JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
JOIN projects p ON lp."projectId" = p.id
LEFT JOIN languages l ON p."languageId" = l.id
LEFT JOIN countries c ON p."countryId" = c.id
WHERE p.name = 'Ginuman_Lit.'
  AND lpg.version > 1
ORDER BY lg."genreId", lpg.version DESC
"""

df = db_manager.execute_query(query)

print("\n📊 DETAILED GENRE ANALYSIS:")
print("="*80)

for _, row in df.iterrows():
    print(f"\n📖 Genre: {row['genre_name']} ({row['genre_type']})")
    print(f"   Version: {row['version']}")
    
    content = row['content']
    if content:
        try:
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content
            
            if 'content' in data and isinstance(data['content'], list):
                blocks = data['content']
                total_blocks = len(blocks)
                
                # Analyze each block
                blocks_with_content = 0
                total_sentences = 0
                empty_blocks = 0
                
                block_details = []
                for i, block in enumerate(blocks):
                    if isinstance(block, dict):
                        text = block.get('content', '')
                        if text and text.strip():
                            blocks_with_content += 1
                            # Count sentences in this block
                            import re
                            sentences = re.split(r'[.!?]+', text)
                            sentence_count = len([s for s in sentences if s.strip()])
                            total_sentences += sentence_count
                            block_details.append({
                                'index': i + 1,
                                'title': block.get('title', '')[:30],
                                'sentences': sentence_count,
                                'characters': len(text),
                                'preview': text[:50] + '...' if len(text) > 50 else text
                            })
                        else:
                            empty_blocks += 1
                
                print(f"   📊 Statistics:")
                print(f"      Total Content Blocks: {total_blocks}")
                print(f"      Blocks with Content: {blocks_with_content}")
                print(f"      Empty Blocks: {empty_blocks}")
                print(f"      Fill Rate: {blocks_with_content/total_blocks*100:.1f}%")
                print(f"      Total Sentences: {total_sentences}")
                print(f"      Avg Sentences per Block (with content): {total_sentences/blocks_with_content:.1f}" if blocks_with_content > 0 else "      Avg Sentences per Block: N/A")
                
                # Show first 3 blocks with content
                if block_details:
                    print(f"\n   📝 Sample Content Blocks:")
                    for detail in block_details[:3]:
                        print(f"      Block {detail['index']}: {detail['sentences']} sentences - '{detail['preview']}'")
                
        except Exception as e:
            print(f"   Error parsing content: {e}")

print("\n" + "="*80)
print("RECOMMENDED METRICS FOR LITERATURE:")
print("="*80)
print("""
Based on the analysis, the most meaningful metrics are:

1. 📊 FILL RATE: Percentage of content blocks that have ANY text
   - This tells you how much of the literature piece is populated
   - Example: Poetry has 44/264 blocks filled (16.7% fill rate)

2. 📝 SENTENCE COUNT: Total number of sentences translated
   - This is the actual content volume

3. 📖 COMPLETION STATUS:
   - Not Started: 0% fill rate
   - In Progress: 1-99% fill rate
   - Completed: 100% fill rate

4. 🎯 QUALITY INDICATORS:
   - Average sentences per filled block (indicates detail level)
   - Total characters/words translated

The current "Completion %" showing 100% for Poetry is INCORRECT because:
- It's comparing sentences to blocks (apples to oranges)
- Should be comparing FILLED BLOCKS to TOTAL BLOCKS
""")
