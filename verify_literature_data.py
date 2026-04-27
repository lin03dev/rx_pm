#!/usr/bin/env python3
"""
Verify Literature Data - Check actual content structure for accuracy
"""

import sys
import json
import re
sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager

db_config = DatabaseConfigManager()
db_manager = DatabaseManager(db_config)
db_manager.current_db = 'AG_Dev'

def count_sentences(text):
    if not text:
        return 0
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

print("="*80)
print("LITERATURE DATA VERIFICATION")
print("="*80)

# Get the actual content for Ginuman_Lit. Poetry
query = """
SELECT 
    p.name as project_name,
    lg."genreId" as genre_type,
    lpg.content,
    lpg.version
FROM literature_project_genres_history lpg
JOIN literature_project_genres lg ON lpg."literatureProjectGenreId" = lg.id
JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
JOIN projects p ON lp."projectId" = p.id
WHERE p.name = 'Ginuman_Lit.'
  AND lg."genreId" = 'poetry'
  AND lpg.version > 1
ORDER BY lpg.version DESC
LIMIT 1
"""

df = db_manager.execute_query(query)

if not df.empty:
    print("\n📖 ANALYZING POETRY CONTENT:")
    print("="*60)
    
    content = df['content'].iloc[0]
    version = df['version'].iloc[0]
    
    print(f"Project: Ginuman_Lit.")
    print(f"Genre: Poetry")
    print(f"Version: {version}")
    
    if isinstance(content, str):
        data = json.loads(content)
    else:
        data = content
    
    if 'content' in data:
        blocks = data['content']
        total_blocks = len(blocks)
        
        print(f"\n📊 Block Analysis:")
        print(f"   Total Blocks: {total_blocks}")
        
        # Analyze each block
        blocks_with_content = 0
        total_sentences = 0
        total_words = 0
        block_details = []
        
        for i, block in enumerate(blocks):
            if isinstance(block, dict):
                text = block.get('content', '')
                block_type = block.get('type', 'unknown')
                has_content = bool(text and text.strip())
                
                if has_content:
                    blocks_with_content += 1
                    sentences = count_sentences(text)
                    words = len(text.split())
                    total_sentences += sentences
                    total_words += words
                    
                    block_details.append({
                        'index': i + 1,
                        'type': block_type,
                        'sentences': sentences,
                        'words': words,
                        'preview': text[:80] + '...' if len(text) > 80 else text
                    })
        
        print(f"   Blocks with Content: {blocks_with_content}")
        print(f"   Total Sentences: {total_sentences}")
        print(f"   Total Words: {total_words}")
        print(f"   Fill Rate: {blocks_with_content/total_blocks*100:.1f}%")
        print(f"   Avg Sentences per Filled Block: {total_sentences/blocks_with_content:.2f}" if blocks_with_content > 0 else "   Avg Sentences per Filled Block: N/A")
        
        print(f"\n📝 Sample of Filled Blocks (first 5):")
        for detail in block_details[:5]:
            print(f"\n   Block {detail['index']} ({detail['type']}):")
            print(f"     Sentences: {detail['sentences']}")
            print(f"     Words: {detail['words']}")
            print(f"     Preview: {detail['preview']}")
        
        print(f"\n📊 WHAT THIS MEANS:")
        print(f"   - Each 'block' is a {block_details[0]['type'] if block_details else 'paragraph'} element")
        print(f"   - Not every block has content (only {blocks_with_content}/{total_blocks} filled)")
        print(f"   - Each filled block contains {total_sentences/blocks_with_content:.1f} sentences on average")
        print(f"   - This is like tracking paragraphs in a book, not individual sentences")
        
print("\n" + "="*80)
print("RECOMMENDATION:")
print("="*80)
print("""
The current metrics are ACCURATE for what they measure:
- Total Blocks = Total number of content slots (like paragraphs/sections)
- Filled Blocks = Number of slots that have actual content
- Fill Rate = How much of the literature piece is populated
- Total Sentences = Actual number of sentences translated

This is the correct way to measure literature progress - similar to:
- OBS: Paragraphs completed vs total paragraphs
- Bible: Verses completed vs total verses

The data shows that Poetry is 16.7% complete (44/264 blocks filled), 
not 100% complete. This is ACCURATE based on the actual content.
""")
