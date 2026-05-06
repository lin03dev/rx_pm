#!/usr/bin/env python3
"""
Dynamic Reporting System - Main Entry Point with Complete LMS and Language Survey Support
"""

import sys
import argparse
import yaml
import os
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from config.database_config import DatabaseConfigManager
from config.output_config import get_output_config
from core.database_manager import DatabaseManager
from core.report_engine import ReportEngine
from utils.logger import setup_logger

logger = setup_logger(__name__)


def load_config(config_file: str = "config/system_config.yaml") -> dict:
    """Load configuration from YAML file"""
    config_path = Path(config_file)
    default_config = {
        'output': {
            'default_path': './output/reports',
            'timestamp_format': '%Y%m%d_%H%M%S',
            'subdirectories': {
                'AG': './output/reports/AG',
                'LMS': './output/reports/LMS',
                'Telios': './output/reports/Telios',
                'Language': './output/reports/Language'
            }
        },
        'templates': {
            'default_path': './output/templates',
            'subdirectories': {
                'AG': './output/templates/AG',
                'LMS': './output/templates/LMS',
                'Telios': './output/templates/Telios',
                'Language': './output/templates/Language'
            }
        }
    }
    
    if config_path.exists():
        with open(config_file, 'r') as f:
            user_config = yaml.safe_load(f)
            if user_config:
                for key in user_config:
                    if key in default_config and isinstance(default_config[key], dict):
                        default_config[key].update(user_config[key])
                    else:
                        default_config[key] = user_config[key]
    
    # Create output directories
    for subdir in default_config['output']['subdirectories'].values():
        Path(subdir).mkdir(parents=True, exist_ok=True)
    
    for subdir in default_config['templates']['subdirectories'].values():
        Path(subdir).mkdir(parents=True, exist_ok=True)
    
    return default_config


def get_output_path(config: dict, database_name: str, report_name: str, format_type: str) -> Path:
    """Get the appropriate output path based on database"""
    output_config = get_output_config()
    category = output_config.get_database_category(database_name)
    output_folder = output_config.get_output_folder(database_name)
    output_root = config['output']['subdirectories'].get(output_folder, config['output']['default_path'])
    
    timestamp = datetime.now().strftime(config['output']['timestamp_format'])
    extension = {'excel': 'xlsx', 'csv': 'csv', 'json': 'json'}.get(format_type, 'xlsx')
    filename = f"{report_name}_{timestamp}.{extension}"
    
    return Path(output_root) / filename


def register_reports(report_engine):
    """Register all available reports"""
    registered = []
    
    reports_to_try = [
        # AG_Dev Reports
        ('user', 'reports.user_report', 'UserReport'),
        ('custom', 'reports.custom_report', 'CustomReport'),
        ('individual', 'reports.individual_performance_report', 'IndividualPerformanceReport'),
        ('consolidated', 'reports.consolidated_report_dynamic', 'ConsolidatedReportDynamic'),
        ('bible-completion', 'reports.bible_project_completion_report', 'BibleProjectCompletionReport'),
        ('obs-completion', 'reports.obs_project_completion_report', 'OBSProjectCompletionReport'),
        ('literature-completion', 'reports.literature_project_completion_report', 'LiteratureProjectCompletionReport'),
        ('grammar-completion', 'reports.grammar_project_completion_report', 'GrammarProjectCompletionReport'),
        ('worklog', 'reports.worklog_report', 'WorklogReport'),
        ('user-activity', 'reports.user_activity_report', 'UserActivityReport'),
        ('user-assignments', 'reports.user_assignment_report', 'UserAssignmentReport'),
        ('literature-genre', 'reports.literature_genre_report', 'LiteratureGenreReport'),
        ('ag-drafting', 'reports.ag_drafting_monitoring_report', 'AGDraftingMonitoringReport'),
        
        # LMS Reports
        ('lms', 'reports.lms_report', 'LMSReport'),
        ('lms-batch', 'reports.batch_detailed_report', 'BatchDetailedReport'),
        
        # Language Survey Reports
        ('language-survey', 'reports.language_survey_report', 'LanguageSurveyReport'),
        ('language-dashboard', 'reports.language_dashboard', 'LanguageDashboard'),
    ]
    
    for report_name, module_path, class_name in reports_to_try:
        try:
            module = __import__(module_path, fromlist=[class_name])
            report_class = getattr(module, class_name)
            if report_class is not None:
                report_engine.register_report(report_name, report_class)
                registered.append(report_name)
        except (ImportError, AttributeError) as e:
            pass
    
    return registered


def generate_lms_batch_reports(db_manager):
    """Generate detailed batch reports for all LMS batches"""
    try:
        from generate_lms_batch_reports import main as generate_batches
        print("\n📊 Generating LMS Batch Reports...")
        generate_batches()
        return True
    except Exception as e:
        print(f"⚠️ Could not generate LMS batch reports: {e}")
        return False


def generate_language_templates():
    """Generate language survey templates"""
    try:
        print("\n📋 Generating Language Survey Templates...")
        subprocess.run([sys.executable, "generate_dynamic_hierarchical_workbook.py"], 
                      capture_output=True, text=True)
        return True
    except Exception as e:
        print(f"⚠️ Could not generate language templates: {e}")
        return False


def generate_lms_templates():
    """Generate LMS templates"""
    try:
        print("\n📋 Generating LMS Templates...")
        subprocess.run([sys.executable, "generate_lms_templates.py"], 
                      capture_output=True, text=True)
        return True
    except Exception as e:
        print(f"⚠️ Could not generate LMS templates: {e}")
        return False


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
  python run.py --report lms --database Telios_LMS_Dev
  python run.py --report lms-batch --database Telios_LMS_Dev
  
  # Generate Language Survey reports
  python run.py --report language-survey --database Telios_LMS_Dev
  python run.py --report language-dashboard --database Telios_LMS_Dev
  
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
            print(f"      Output: output/reports/{category}/")
        return
    
    # Handle list databases
    if args.list_databases:
        db_config_manager = DatabaseConfigManager()
        print("\n📚 Available Databases:")
        print("=" * 60)
        for db_name in db_config_manager.list_databases():
            config = db_config_manager.get_config(db_name)
            category = output_config.get_database_category(db_name)
            output_folder = output_config.get_output_folder(db_name)
            print(f"\n   🔹 {db_name}")
            print(f"      Category: {category}")
            print(f"      Output: output/reports/{output_folder}/")
            print(f"      Host: {config.host}")
        return
    
    # Handle list reports
    if args.list_reports:
        print("\n📊 Available Reports by Category:")
        print("=" * 60)
        print("\n📁 AG_Dev Database Reports:")
        print("   • bible-completion - Bible translation progress")
        print("   • obs-completion - OBS translation progress")
        print("   • literature-completion - Literature genre completion")
        print("   • grammar-completion - Grammar projects")
        print("   • ag-drafting - AG Drafting Monitoring Report")
        print("   • consolidated - All project types combined")
        print("   • user - User management report")
        print("   • worklog - Work tracking report")
        print("   • individual - Individual performance by person")
        print("   • user-activity - User activity tracking")
        print("   • user-assignments - User assignments across projects")
        print("   • literature-genre - Literature genre details")
        print("\n📁 Telios_LMS Database Reports:")
        print("   • lms - LMS summary report")
        print("   • lms-batch - Detailed batch reports (87 batches, 11 sheets each)")
        print("\n📁 Language Survey Reports:")
        print("   • language-survey - Language survey analysis report")
        print("   • language-dashboard - Consolidated language dashboard")
        print("\n📁 Utility:")
        print("   • custom - Execute custom SQL queries")
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
        
        # Generate AG_Dev reports
        print("\n📊 AG_Dev Reports:")
        subprocess.run([sys.executable, "run_all.sh"])
        
        # Generate templates
        generate_lms_templates()
        generate_language_templates()
        
        print("\n✅ Complete! Check output/reports/ and output/templates/")
        return
    
    # Handle regular report generation
    if args.report and args.database:
        db_manager = DatabaseManager(DatabaseConfigManager())
        db_manager.current_db = args.database
        
        class CustomReportEngine(ReportEngine):
            def generate_report(self, report_name, output_format='excel', filters=None, db_name=None, **kwargs):
                report = self.get_report(report_name, db_name=db_name, **kwargs)
                if filters:
                    report.apply_filters(filters)
                data = report.generate()
                output_file = str(get_output_path(config, db_name, report_name, output_format))
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                
                if output_format == 'excel':
                    self._save_as_excel(data, output_file, report.get_sheet_names())
                elif output_format == 'csv':
                    self._save_as_csv(data, output_file)
                elif output_format == 'json':
                    self._save_as_json(data, output_file)
                
                logger.info(f"Report generated: {output_file}")
                return output_file
        
        config = load_config()
        report_engine = CustomReportEngine(db_manager, config)
        registered = register_reports(report_engine)
        
        category = output_config.get_database_category(args.database)
        output_folder = output_config.get_output_folder(args.database)
        
        print(f"\n📊 Generating {args.report.upper()} report...")
        print(f"   Database: {args.database}")
        print(f"   Category: {category}")
        print(f"   Format: {args.format}")
        print(f"   Output: output/reports/{output_folder}/")
        
        try:
            output_file = report_engine.generate_report(
                report_name=args.report,
                output_format=args.format,
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
