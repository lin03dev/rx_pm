#!/usr/bin/env python3
"""
Dynamic Reporting System - Main Entry Point with Complete LMS and Language Survey Support
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from config.database_config import DatabaseConfigManager
from config.output_config import get_output_config
from config.report_registry import grouped_configured_reports, register_configured_reports
from core.database_manager import DatabaseManager
from core.report_engine import ReportEngine
from utils.logger import setup_logger

logger = setup_logger(__name__)
BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
SCRIPTS_DIR = BACKEND_DIR / "scripts"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def load_config(config_file: str | Path = BACKEND_DIR / "config" / "system_config.yaml") -> dict:
    """Backward-compatible wrapper."""
    from config.system_loader import load_config as _load_config

    return _load_config(config_file)


def _run_script(script_name: str) -> bool:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        logger.warning("Script not found: %s", script_path)
        return False
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.warning("Script failed (%s): %s", script_name, result.stderr.strip() or result.stdout.strip())
        return False
    return True


def generate_lms_batch_reports(db_manager=None):
    """Generate detailed batch reports for all LMS batches."""
    try:
        print("\n📊 Generating LMS Batch Reports...")
        from scripts.generate_lms_batch_reports import main as generate_batches

        generate_batches()
        return True
    except Exception as exc:
        print(f"⚠️ Could not generate LMS batch reports: {exc}")
        return False


def generate_language_templates():
    """Generate language survey templates."""
    print("\n📋 Generating Language Survey Templates...")
    return _run_script("generate_dynamic_workbook.py")


def generate_lms_templates():
    """Generate LMS templates."""
    print("\n📋 Generating LMS Templates...")
    return _run_script("generate_lms_templates.py")


def run_batch_pipeline():
    """Run the full offline report generation pipeline."""
    if sys.platform == "win32":
        command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(BACKEND_DIR / "run_all.ps1")]
    else:
        command = ["bash", str(BACKEND_DIR / "run_all.sh")]
    result = subprocess.run(command, cwd=str(REPO_ROOT))
    return result.returncode == 0


def get_output_path(config: dict, database_name: str, report_name: str, format_type: str) -> Path:
    """Get the appropriate output path based on database"""
    output_config = get_output_config()
    output_root = output_config.get_output_path(database_name)

    timestamp = datetime.now().strftime(config['output']['timestamp_format'])
    extension = {'excel': 'xlsx', 'csv': 'csv', 'json': 'json'}.get(format_type, 'xlsx')
    filename = f"{report_name}_{timestamp}.{extension}"

    return Path(output_root) / filename


def register_reports(report_engine):
    """Register all available reports"""
    return register_configured_reports(report_engine)


def main():
    parser = argparse.ArgumentParser(
        description='Dynamic Reporting System - Complete Reporting Solution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available resources
  python run.py --list-reports
  python run.py --list-databases
  python run.py --list-categories
  
  # Generate AG_Dev reports
  python run.py --report user --database AG_Dev
  python run.py --report consolidated --database AG_Dev
  python run.py --all --database AG_Dev
  
  # Generate LMS reports
  python run.py --report bt-academy-students --database LMS_Dev
  python run.py --report lms --database LMS_Dev
  python run.py --report lms-batch --database LMS_Dev
  
  # Generate Language Survey reports
  python run.py --report language-survey --database LMS_Dev
  python run.py --report language-dashboard --database LMS_Dev
  
  # Generate all reports and templates
  python run.py --generate-all
  python run.py --generate-templates
        """
    )
    
    parser.add_argument('--report', '-r', help='Type of report to generate')
    parser.add_argument('--database', '-db', help='Database to use')
    parser.add_argument('--format', '-f', choices=['excel', 'csv', 'json'], default='excel')
    parser.add_argument('--output', '-o', help='Output directory (overrides default)')
    parser.add_argument('--query', '-q', help='Custom SQL query (for custom reports)')
    parser.add_argument('--filters', '-filter', nargs='*', help='Filters in format key=value')
    parser.add_argument('--list-reports', '-l', action='store_true', help='List all available reports')
    parser.add_argument('--list-databases', '-ld', action='store_true', help='List all available databases')
    parser.add_argument('--list-categories', '-lc', action='store_true', help='List all output categories')
    parser.add_argument('--all', '-a', action='store_true', help='Generate all reports for specified database')
    parser.add_argument('--all-lms', action='store_true', help='Generate all LMS reports (summary + batch details)')
    parser.add_argument('--generate-templates', '-gt', action='store_true', help='Generate all templates')
    parser.add_argument('--generate-all', '-ga', action='store_true', help='Generate all reports and templates')
    
    args = parser.parse_args()
    
    output_config = get_output_config()
    
    # Handle list categories
    if args.list_categories:
        print("\n📁 Output Categories:")
        print("=" * 50)
        for category in output_config.list_categories():
            info = output_config.get_category_info(category)
            databases = info.get("databases", [])
            print(f"\n   📂 {category}/")
            print(f"      Databases: {', '.join(databases) if databases else 'None'}")
            reports_path = info.get("reports_path") or f"output/reports/{category}/"
            print(f"      Output: {reports_path}")
        return
    
    # Handle list databases
    if args.list_databases:
        db_config_manager = DatabaseConfigManager()
        print("\n📚 Available Databases:")
        print("=" * 60)
        for db_name in db_config_manager.list_databases():
            config = db_config_manager.get_config(db_name)
            category = output_config.get_database_category(db_name)
            print(f"\n   🔹 {db_name}")
            print(f"      Category: {category}")
            print(f"      Output: {output_config.get_output_path(db_name)}")
            print(f"      Host: {config.host}")
        return
    
    # Handle list reports
    if args.list_reports:
        print("\nReports by Category:")
        print("=" * 60)
        for _, category_info, reports in grouped_configured_reports():
            print(f"\n{category_info.get('display_name', 'Reports')}:")
            for report in reports:
                print(f"   - {report['id']} - {report['description']}")
        print("=" * 60)
        return

    # Handle generate templates
    if args.generate_templates:
        print("\n📋 Generating all templates...")
        print("=" * 60)
        generate_lms_templates()
        generate_language_templates()
        print("\n✅ Template generation complete!")
        return
    
    # Handle generate all
    if args.generate_all:
        print("\n🚀 Generating everything...")
        print("=" * 60)
        run_batch_pipeline()
        generate_lms_templates()
        generate_language_templates()
        print("\n✅ Complete! Check output/reports/ and output/templates/")
        return
    
    # Handle regular report generation
    if args.report and args.database:
        filters = {}
        if args.filters:
            for item in args.filters:
                if '=' in item:
                    key, value = item.split('=', 1)
                    filters[key] = value

        config = load_config()
        db_manager = DatabaseManager(DatabaseConfigManager())
        db_manager.current_db = args.database

        class CustomReportEngine(ReportEngine):
            def generate_report(self, report_name, output_format='excel', filters=None, db_name=None, **kwargs):
                report = self.get_report(report_name, db_name=db_name, **kwargs)
                if filters:
                    report.apply_filters(filters)
                data = report.generate()
                output_file = str(get_output_path(self.config, db_name, report_name, output_format))
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                
                if output_format == 'excel':
                    from config.report_schema import apply_schema_output, resolve_sheet_names
                    data = apply_schema_output(report_name, data)
                    sheet_names = resolve_sheet_names(report_name, report.get_sheet_names())
                    self._save_as_excel(data, output_file, sheet_names, report_name=report_name)
                elif output_format == 'csv':
                    self._save_as_csv(data, output_file)
                elif output_format == 'json':
                    self._save_as_json(data, output_file)
                
                logger.info(f"Report generated: {output_file}")
                return output_file

        report_engine = CustomReportEngine(db_manager, config)
        registered = register_reports(report_engine)
        
        category = output_config.get_database_category(args.database)
        output_path = output_config.get_output_path(args.database)
        
        print(f"\n📊 Generating {args.report.upper()} report...")
        print(f"   Database: {args.database}")
        print(f"   Category: {category}")
        print(f"   Format: {args.format}")
        print(f"   Output: {output_path}")
        
        try:
            output_file = report_engine.generate_report(
                report_name=args.report,
                output_format=args.format,
                filters=filters,
                db_name=args.database
            )
            print(f"\n✅ Report generated successfully!")
            print(f"   📁 Location: {output_file}")
        except Exception as e:
            print(f"\n❌ Failed to generate report: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    import pandas as pd
    main()
