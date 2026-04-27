#!/usr/bin/env python3
"""
Dynamic Reporting System - Main Entry Point
"""

import sys
import argparse
import yaml
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager
from core.report_engine import ReportEngine
from reports.user_report import UserReport
from reports.worklog_report import WorklogReport
from reports.custom_report import CustomReport
from reports.individual_performance_report import IndividualPerformanceReport
from reports.bible_project_completion_report import BibleProjectCompletionReport
from reports.obs_project_completion_report import OBSProjectCompletionReport
from reports.literature_project_completion_report import LiteratureProjectCompletionReport
from reports.grammar_project_completion_report import GrammarProjectCompletionReport
from reports.lms_report import LMSReport
from reports.user_assignment_report import UserAssignmentReport
from reports.consolidated_project_report import ConsolidatedProjectReport
from reports.literature_genre_report import LiteratureGenreReport
from reports.user_activity_report import UserActivityReport
from reports.ag_drafting_monitoring_report import AGDraftingMonitoringReport
from utils.logger import setup_logger

logger = setup_logger(__name__)


def load_config(config_file: str = "config/system_config.yaml") -> dict:
    """Load configuration from YAML file"""
    config_path = Path(config_file)
    default_config = {
        'output': {
            'default_path': './output/reports',
            'timestamp_format': '%Y%m%d_%H%M%S'
        }
    }
    
    if config_path.exists():
        with open(config_file, 'r') as f:
            user_config = yaml.safe_load(f)
            if user_config:
                if 'output' in user_config:
                    default_config['output'].update(user_config['output'])
    
    Path(default_config['output']['default_path']).mkdir(parents=True, exist_ok=True)
    
    return default_config


def main():
    parser = argparse.ArgumentParser(
        description='Dynamic Reporting System - Generate reports from local databases',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # AG_Dev Reports
  python run.py --report bible-completion --database AG_Dev
  python run.py --report obs-completion --database AG_Dev
  python run.py --report literature-completion --database AG_Dev
  python run.py --report grammar-completion --database AG_Dev
  python run.py --report individual --database AG_Dev
  python run.py --report worklog --database AG_Dev
  python run.py --report user --database AG_Dev
  python run.py --report user-assignments --database AG_Dev
  python run.py --report consolidated --database AG_Dev
  python run.py --report literature-genre --database AG_Dev
  python run.py --report user-activity --database AG_Dev
  python run.py --report ag-drafting --database AG_Dev
  
  # Telios_LMS Reports
  python run.py --report lms --database Telios_LMS_Dev
  
  # Custom Query
  python run.py --report custom --database AG_Dev --query "SELECT * FROM users LIMIT 10"
  
  # List available resources
  python run.py --list-reports
  python run.py --list-databases
        """
    )
    
    parser.add_argument('--report', '-r', 
                       choices=[
                           'user', 'worklog', 'custom', 'individual',
                           'bible-completion', 'obs-completion', 
                           'literature-completion', 'grammar-completion',
                           'user-assignments', 'consolidated', 'literature-genre',
                           'user-activity', 'ag-drafting', 'lms'
                       ],
                       help='Type of report to generate')
    
    parser.add_argument('--database', '-db', 
                       help='Database to use (AG_Dev, Telios_LMS_Dev)')
    
    parser.add_argument('--format', '-f', 
                       choices=['excel', 'csv', 'json'],
                       default='excel',
                       help='Output format (default: excel)')
    
    parser.add_argument('--output', '-o', 
                       help='Output directory for reports')
    
    parser.add_argument('--query', '-q', 
                       help='Custom SQL query (for custom reports)')
    
    parser.add_argument('--filters', '-filter', nargs='*',
                       help='Filters in format key=value (e.g., role=MTT)')
    
    parser.add_argument('--list-reports', '-l', action='store_true',
                       help='List all available reports')
    
    parser.add_argument('--list-databases', '-ld', action='store_true',
                       help='List all available databases')
    
    args = parser.parse_args()
    
    # Handle list databases
    if args.list_databases:
        db_config_manager = DatabaseConfigManager()
        print("\n📚 Available Databases:")
        print("=" * 50)
        for db_name in db_config_manager.list_databases():
            config = db_config_manager.get_config(db_name)
            print(f"   • {db_name}")
            print(f"     Project: {config.project}")
            print(f"     Database: {config.database}")
            print(f"     Host: {config.host}")
            print()
        return
    
    # Handle list reports
    if args.list_reports:
        print("\n📊 Available Reports:")
        print("=" * 60)
        print("\n📁 AG_Dev Reports:")
        print("   • bible-completion - Bible translation progress (verses + chapters)")
        print("   • obs-completion - OBS translation (chapters + paragraphs + audio)")
        print("   • literature-completion - Literature genre completion (project level)")
        print("   • literature-genre - Literature genre details (1 row per genre)")
        print("   • grammar-completion - Grammar projects (phrases, pronouns, connectives)")
        print("   • individual - Individual performance by person")
        print("   • worklog - Work tracking report")
        print("   • user - User management report")
        print("   • user-assignments - Complete user assignments across all projects")
        print("   • user-activity - User activity tracking (start date, last use, project roles)")
        print("   • consolidated - All project types in one consolidated view")
        print("   • ag-drafting - AG Drafting Monitoring Report (all projects combined)")
        print("\n📁 Telios_LMS Reports:")
        print("   • lms - LMS batch, enrollment, attendance report")
        print("\n📁 Utility:")
        print("   • custom - Execute custom SQL queries")
        print("=" * 60)
        return
    
    # Load configuration
    config = load_config()
    
    if args.output:
        config['output']['default_path'] = args.output
    
    db_config_manager = DatabaseConfigManager()
    
    if not args.database:
        print("❌ Error: --database parameter is required")
        print("   Available databases:")
        for db_name in db_config_manager.list_databases():
            print(f"     - {db_name}")
        sys.exit(1)
    
    if args.database not in db_config_manager.list_databases():
        print(f"❌ Database '{args.database}' not found.")
        print(f"   Available: {', '.join(db_config_manager.list_databases())}")
        sys.exit(1)
    
    db_manager = DatabaseManager(db_config_manager)
    report_engine = ReportEngine(db_manager, config)
    
    # Register reports
    report_engine.register_report('user', UserReport)
    report_engine.register_report('worklog', WorklogReport)
    report_engine.register_report('custom', CustomReport)
    report_engine.register_report('individual', IndividualPerformanceReport)
    report_engine.register_report('bible-completion', BibleProjectCompletionReport)
    report_engine.register_report('obs-completion', OBSProjectCompletionReport)
    report_engine.register_report('literature-completion', LiteratureProjectCompletionReport)
    report_engine.register_report('grammar-completion', GrammarProjectCompletionReport)
    report_engine.register_report('lms', LMSReport)
    report_engine.register_report('user-assignments', UserAssignmentReport)
    report_engine.register_report('consolidated', ConsolidatedProjectReport)
    report_engine.register_report('literature-genre', LiteratureGenreReport)
    report_engine.register_report('user-activity', UserActivityReport)
    report_engine.register_report('ag-drafting', AGDraftingMonitoringReport)
    
    # Generate custom report
    if args.report == 'custom':
        if not args.query:
            print("❌ Error: Custom report requires --query parameter")
            sys.exit(1)
        
        output_file = report_engine.generate_custom_report(
            query=args.query,
            report_name=f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            output_format=args.format,
            db_name=args.database
        )
        print(f"\n✅ Custom report generated: {output_file}")
        return
    
    # Generate predefined report
    if args.report:
        filters = {}
        if args.filters:
            for filter_item in args.filters:
                if '=' in filter_item:
                    key, value = filter_item.split('=', 1)
                    filters[key] = value
        
        print(f"\n📊 Generating {args.report.upper()} report...")
        print(f"   Database: {args.database}")
        print(f"   Format: {args.format}")
        if filters:
            print(f"   Filters: {filters}")
        
        output_file = report_engine.generate_report(
            report_name=args.report,
            output_format=args.format,
            filters=filters,
            db_name=args.database
        )
        print(f"\n✅ Report generated successfully!")
        print(f"   📁 Location: {output_file}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
