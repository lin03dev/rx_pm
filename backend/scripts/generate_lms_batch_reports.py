#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
"""
Generate detailed batch reports for all LMS batches with conditional formatting
"""

import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager
from reports.batch_detailed_report import BatchDetailedReport
from utils.report_excel_writer import get_report_excel_writer

def main():
    print("="*80)
    print("LMS BATCH DETAILED REPORT GENERATOR")
    print("="*80)
    
    # Setup
    db_config = DatabaseConfigManager()
    db_manager = DatabaseManager(db_config)
    db_manager.current_db = 'LMS_Dev'
    
    # Output base directory
    base_output_dir = Path("./output/reports/LMS/Batch_Reports")
    base_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all batches
    query = """
    SELECT 
        b.id as batch_id,
        b.batch as batch_name,
        COALESCE(c.title, 'Uncategorized') as course_name
    FROM batch b
    LEFT JOIN course c ON COALESCE(b.course_id, b.course) = c.id
    WHERE b.id IS NOT NULL
    ORDER BY course_name, b.batch
    """
    
    batches_df = db_manager.execute_query(query)
    
    if batches_df.empty:
        print("❌ No batches found!")
        return
    
    print(f"\n📊 Found {len(batches_df)} batches")
    
    successful = 0
    failed = 0
    batches_with_attendance = 0
    excel_writer = get_report_excel_writer()
    
    for idx, batch in batches_df.iterrows():
        course_name = batch['course_name'] if pd.notna(batch['course_name']) else 'Uncategorized'
        batch_name = batch['batch_name']
        batch_id = batch['batch_id']
        
        # Clean folder name
        clean_course = str(course_name).replace('/', '_').replace('\\', '_').replace(' ', '_')
        course_folder = base_output_dir / clean_course
        course_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"\n[{idx+1}/{len(batches_df)}] {course_name} → {batch_name}")
        
        try:
            report = BatchDetailedReport(
                db_manager,
                batch_id=batch_id,
                report_id="lms-batch",
                db_name="LMS_Dev",
            )
            report_data = report.generate()
            
            if 'error' not in report_data:
                filename = report.get_filename()
                output_path = course_folder / filename
                
                from config.report_schema import apply_schema_output, resolve_sheet_names
                report_data = apply_schema_output("lms-batch", report_data)
                sheet_names = resolve_sheet_names("lms-batch", report.get_sheet_names())
                excel_writer.save_report(
                    output_path,
                    report_data,
                    sheet_names,
                    report_id="lms-batch",
                )
                
                # Check if this batch has attendance data
                if 'attendance_matrix' in report_data and len(report_data['attendance_matrix']) > 0:
                    if 'Message' not in report_data['attendance_matrix'].columns:
                        batches_with_attendance += 1
                
                print(f"   ✅ Generated (with conditional formatting)")
                successful += 1
            else:
                print(f"   ❌ Error: {report_data['error']}")
                failed += 1
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📋 Batches with Attendance Data: {batches_with_attendance}")
    print(f"📁 Output: {base_output_dir}")
    print("="*80)
    
    # Show summary by course
    print("\n📂 Reports by Course:")
    for course_dir in sorted(base_output_dir.iterdir()):
        if course_dir.is_dir():
            report_count = len(list(course_dir.glob("*.xlsx")))
            if report_count > 0:
                print(f"   • {course_dir.name}: {report_count} report(s)")

if __name__ == '__main__':
    main()
