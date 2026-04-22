#!/usr/bin/env python3
"""
Unified Reporting & Data Management System
Single entry point for reports, templates, and data uploads
"""

import sys
import argparse
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

sys.path.insert(0, str(Path(__file__).parent))

from config.database_config import DatabaseConfigManager
from config.excel_template_config import TemplatePurpose, get_excel_template_manager
from config.project_type_config import get_project_type_config_manager
from config.report_templates import get_report_template_config

from core.database_manager import DatabaseManager
from core.report_engine import ReportEngine
from core.template_uploader import TemplateUploader

from reports.user_report import UserReport
from reports.worklog_report import WorklogReport
from reports.custom_report import CustomReport
from reports.individual_performance_report import IndividualPerformanceReport
from reports.bible_project_completion_report import BibleProjectCompletionReport
from reports.obs_project_completion_report import OBSProjectCompletionReport
from reports.literature_project_completion_report import LiteratureProjectCompletionReport
from reports.grammar_project_completion_report import GrammarProjectCompletionReport

from utils.excel_template_generator import get_excel_template_generator, ExcelTemplateValidator
from utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)


class UnifiedSystem:
    """Unified system for reports, templates, and data management"""
    
    def __init__(self, config_file: str = "config/system_config.yaml"):
        self.config = self._load_config(config_file)
        self.db_config_manager = DatabaseConfigManager()
        self.db_manager = None
        self.report_engine = None
        self.template_generator = get_excel_template_generator()
        self.template_validator = ExcelTemplateValidator()
        self.template_manager = get_excel_template_manager()
        
    def _load_config(self, config_file: str) -> dict:
        """Load system configuration"""
        config_path = Path(config_file)
        default_config = {
            'output': {
                'reports_path': './output/reports',
                'templates_path': './output/templates',
                'uploads_path': './output/uploads',
                'logs_path': './output/logs',
                'timestamp_format': '%Y%m%d_%H%M%S'
            },
            'database': {
                'default': 'AG_Dev'
            },
            'reports': {
                'default_format': 'excel',
                'max_rows': 50000
            },
            'templates': {
                'auto_generate_on_startup': False,
                'include_example_data': True
            },
            'uploads': {
                'max_file_size_mb': 50,
                'allowed_extensions': ['.xlsx', '.xls'],
                'require_approval': True
            }
        }
        
        if config_path.exists():
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    self._deep_merge(default_config, user_config)
        
        # Create output directories
        for path_key in ['reports_path', 'templates_path', 'uploads_path', 'logs_path']:
            Path(default_config['output'][path_key]).mkdir(parents=True, exist_ok=True)
        
        return default_config
    
    def _deep_merge(self, base: dict, override: dict):
        """Deep merge two dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _init_db(self, db_name: str = None):
        """Initialize database connection"""
        db_name = db_name or self.config['database']['default']
        if self.db_manager is None or self.db_manager.current_db != db_name:
            self.db_manager = DatabaseManager(self.db_config_manager)
            self.db_manager.current_db = db_name
            self.report_engine = ReportEngine(self.db_manager, self.config)
            self._register_reports()
    
    def _register_reports(self):
        """Register all available reports"""
        self.report_engine.register_report('user', UserReport)
        self.report_engine.register_report('worklog', WorklogReport)
        self.report_engine.register_report('custom', CustomReport)
        self.report_engine.register_report('individual', IndividualPerformanceReport)
        self.report_engine.register_report('bible-completion', BibleProjectCompletionReport)
        self.report_engine.register_report('obs-completion', OBSProjectCompletionReport)
        self.report_engine.register_report('literature-completion', LiteratureProjectCompletionReport)
        self.report_engine.register_report('grammar-completion', GrammarProjectCompletionReport)
    
    # ============================================================
    # Report Generation Methods
    # ============================================================
    
    def generate_report(self, report_name: str, db_name: str = None, 
                       output_format: str = None, filters: Dict = None,
                       output_file: str = None) -> str:
        """Generate a report"""
        self._init_db(db_name)
        
        output_format = output_format or self.config['reports']['default_format']
        
        output_path = self.report_engine.generate_report(
            report_name=report_name,
            output_format=output_format,
            filters=filters,
            db_name=db_name
        )
        
        return output_path
    
    def list_reports(self) -> List[Dict]:
        """List all available reports with details"""
        self._init_db()
        reports = []
        
        report_info = {
            'user': {'name': 'User Report', 'description': 'User management and assignments', 'filters': ['role', 'country']},
            'worklog': {'name': 'Worklog Report', 'description': 'Work tracking and productivity', 'filters': ['role', 'stage', 'software']},
            'individual': {'name': 'Individual Performance', 'description': 'Per-person performance across all projects', 'filters': ['user_id', 'role', 'country']},
            'bible-completion': {'name': 'Bible Project Completion', 'description': 'Bible translation progress (verses + chapters)', 'filters': ['project_id', 'user_id', 'country', 'language']},
            'obs-completion': {'name': 'OBS Project Completion', 'description': 'OBS translation + audio progress', 'filters': ['project_id', 'user_id', 'country']},
            'literature-completion': {'name': 'Literature Project Completion', 'description': 'Literature genre completion', 'filters': ['project_id', 'user_id']},
            'grammar-completion': {'name': 'Grammar Project Completion', 'description': 'Grammar phrases/pronouns/connectives', 'filters': ['project_id', 'user_id']},
            'custom': {'name': 'Custom Report', 'description': 'Execute custom SQL queries', 'filters': []}
        }
        
        for key, info in report_info.items():
            reports.append({
                'id': key,
                'name': info['name'],
                'description': info['description'],
                'available_filters': info['filters']
            })
        
        return reports
    
    # ============================================================
    # Template Generation Methods
    # ============================================================
    
    def generate_template(self, template_purpose: str) -> str:
        """Generate a specific Excel template"""
        try:
            purpose = TemplatePurpose(template_purpose)
            file_path = self.template_generator.generate_template(purpose)
            return str(file_path)
        except ValueError as e:
            raise ValueError(f"Invalid template purpose: {template_purpose}. Valid: {[p.value for p in TemplatePurpose]}")
    
    def generate_all_templates(self) -> List[str]:
        """Generate all Excel templates"""
        return [str(p) for p in self.template_generator.generate_all_templates()]
    
    def list_templates(self) -> List[Dict]:
        """List all available templates"""
        return self.template_manager.list_templates()
    
    # ============================================================
    # Data Upload Methods
    # ============================================================
    
    def upload_data(self, file_path: str, template_purpose: str, 
                    dry_run: bool = False, db_name: str = None) -> Dict:
        """Upload data from Excel template"""
        self._init_db(db_name)
        
        uploader = TemplateUploader(self.db_manager, self.config['output']['uploads_path'])
        
        purpose = TemplatePurpose(template_purpose)
        result = uploader.upload_and_process(file_path, purpose, dry_run)
        
        return result
    
    def validate_upload(self, file_path: str, template_purpose: str) -> Dict:
        """Validate an Excel file before upload"""
        purpose = TemplatePurpose(template_purpose)
        return self.template_validator.validate_upload(file_path, purpose)
    
    # ============================================================
    # Utility Methods
    # ============================================================
    
    def list_databases(self) -> List[Dict]:
        """List all available databases"""
        databases = []
        for db_name in self.db_config_manager.list_databases():
            config = self.db_config_manager.get_config(db_name)
            databases.append({
                'name': db_name,
                'project': config.project,
                'environment': config.environment,
                'host': config.host,
                'description': config.description
            })
        return databases
    
    def test_connection(self, db_name: str) -> Dict:
        """Test database connection"""
        self._init_db(db_name)
        try:
            result = self.db_manager.execute_query("SELECT 1 as test", db_name=db_name)
            return {
                'success': True,
                'message': f'Successfully connected to {db_name}',
                'rows': len(result)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}'
            }
    
    def get_system_info(self) -> Dict:
        """Get system information"""
        return {
            'version': '2.0.0',
            'config': self.config,
            'available_databases': len(self.db_config_manager.list_databases()),
            'available_reports': len(self.list_reports()),
            'available_templates': len(self.list_templates()),
            'output_directories': {
                'reports': self.config['output']['reports_path'],
                'templates': self.config['output']['templates_path'],
                'uploads': self.config['output']['uploads_path'],
                'logs': self.config['output']['logs_path']
            }
        }


# ============================================================
# Command Line Interface
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Unified Reporting & Data Management System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                              COMMAND EXAMPLES                                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  📊 REPORTS:                                                                  ║
║    main.py report --type bible-completion --db AG_Dev                        ║
║    main.py report --type individual --db AG_Dev --format excel               ║
║    main.py report --type worklog --db AG_Dev --filter role=MTT               ║
║    main.py list-reports                                                      ║
║                                                                               ║
║  📋 TEMPLATES:                                                               ║
║    main.py template --generate user_import                                   ║
║    main.py template --generate-all                                           ║
║    main.py list-templates                                                    ║
║                                                                               ║
║  📤 UPLOADS:                                                                 ║
║    main.py upload --file data.xlsx --purpose user_import --db AG_Dev         ║
║    main.py upload --file data.xlsx --purpose worklog_import --dry-run        ║
║    main.py validate --file data.xlsx --purpose assignment_import             ║
║                                                                               ║
║  🔧 UTILITIES:                                                               ║
║    main.py list-databases                                                    ║
║    main.py test-connection --db AG_Dev                                       ║
║    main.py info                                                              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        """
    )
    
    # Subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # ============================================================
    # Report Command
    # ============================================================
    report_parser = subparsers.add_parser('report', help='Generate a report')
    report_parser.add_argument('--type', '-t', required=True, 
                               choices=['user', 'worklog', 'individual', 'bible-completion', 
                                       'obs-completion', 'literature-completion', 
                                       'grammar-completion', 'custom'],
                               help='Type of report to generate')
    report_parser.add_argument('--db', '-d', help='Database name (default: AG_Dev)')
    report_parser.add_argument('--format', '-f', choices=['excel', 'csv', 'json'], 
                               default='excel', help='Output format')
    report_parser.add_argument('--filter', action='append', 
                               help='Filters in format key=value (can be used multiple times)')
    report_parser.add_argument('--query', '-q', help='Custom SQL query (for custom report)')
    report_parser.add_argument('--output', '-o', help='Output file path')
    
    # ============================================================
    # Template Command
    # ============================================================
    template_parser = subparsers.add_parser('template', help='Manage Excel templates')
    template_parser.add_argument('--generate', '-g', 
                                 choices=['user_import', 'project_import', 'assignment_import',
                                         'worklog_import', 'bible_chapter_import', 
                                         'obs_chapter_import', 'literature_genre_import',
                                         'grammar_import'],
                                 help='Generate a specific template')
    template_parser.add_argument('--generate-all', '-a', action='store_true',
                                 help='Generate all templates')
    
    # ============================================================
    # Upload Command
    # ============================================================
    upload_parser = subparsers.add_parser('upload', help='Upload data from Excel template')
    upload_parser.add_argument('--file', '-f', required=True, help='Excel file path')
    upload_parser.add_argument('--purpose', '-p', required=True,
                               choices=['user_import', 'project_import', 'assignment_import',
                                       'worklog_import', 'bible_chapter_import',
                                       'obs_chapter_import', 'literature_genre_import',
                                       'grammar_import'],
                               help='Template purpose')
    upload_parser.add_argument('--db', '-d', help='Database name')
    upload_parser.add_argument('--dry-run', action='store_true',
                               help='Validate without inserting')
    
    # ============================================================
    # Validate Command
    # ============================================================
    validate_parser = subparsers.add_parser('validate', help='Validate Excel file')
    validate_parser.add_argument('--file', '-f', required=True, help='Excel file path')
    validate_parser.add_argument('--purpose', '-p', required=True,
                                 choices=['user_import', 'project_import', 'assignment_import',
                                         'worklog_import', 'bible_chapter_import',
                                         'obs_chapter_import', 'literature_genre_import',
                                         'grammar_import'],
                                 help='Template purpose')
    
    # ============================================================
    # List Commands
    # ============================================================
    subparsers.add_parser('list-reports', help='List all available reports')
    subparsers.add_parser('list-templates', help='List all available templates')
    subparsers.add_parser('list-databases', help='List all available databases')
    
    # ============================================================
    # Utility Commands
    # ============================================================
    test_parser = subparsers.add_parser('test-connection', help='Test database connection')
    test_parser.add_argument('--db', '-d', required=True, help='Database name')
    
    subparsers.add_parser('info', help='Show system information')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize system
    system = UnifiedSystem()
    
    # ============================================================
    # Execute Command
    # ============================================================
    
    # Report commands
    if args.command == 'report':
        # Parse filters
        filters = {}
        if args.filter:
            for f in args.filter:
                if '=' in f:
                    key, value = f.split('=', 1)
                    filters[key] = value
        
        # Handle custom report
        if args.type == 'custom':
            if not args.query:
                print("❌ Error: --query is required for custom report")
                sys.exit(1)
            
            # Create custom report
            system._init_db(args.db)
            output_path = system.report_engine.generate_custom_report(
                query=args.query,
                report_name=f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                output_format=args.format,
                db_name=args.db
            )
            print(f"\n✅ Custom report generated: {output_path}")
        else:
            # Generate regular report
            output_path = system.generate_report(
                report_name=args.type,
                db_name=args.db,
                output_format=args.format,
                filters=filters
            )
            print(f"\n✅ Report generated: {output_path}")
    
    # Template commands
    elif args.command == 'template':
        if args.generate_all:
            files = system.generate_all_templates()
            print(f"\n✅ Generated {len(files)} templates:")
            for f in files:
                print(f"   • {Path(f).name}")
        elif args.generate:
            file_path = system.generate_template(args.generate)
            print(f"\n✅ Template generated: {file_path}")
        else:
            print("❌ Please specify --generate or --generate-all")
    
    # Upload command
    elif args.command == 'upload':
        if not Path(args.file).exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        
        print(f"\n📤 Processing upload...")
        print(f"   File: {args.file}")
        print(f"   Purpose: {args.purpose}")
        if args.dry_run:
            print("   Mode: DRY RUN (validation only)")
        
        result = system.upload_data(
            file_path=args.file,
            template_purpose=args.purpose,
            dry_run=args.dry_run,
            db_name=args.db
        )
        
        if result['success']:
            print(f"\n✅ Upload successful!")
            if not args.dry_run:
                print(f"   Inserted: {result.get('total_inserted', 0)}")
                print(f"   Updated: {result.get('total_updated', 0)}")
                print(f"   Skipped: {result.get('total_skipped', 0)}")
                print(f"   Saved to: {result.get('saved_file', 'N/A')}")
            if result.get('errors'):
                print(f"\n⚠️ Errors: {len(result['errors'])}")
                for err in result['errors'][:5]:
                    print(f"   • {err}")
        else:
            print(f"\n❌ Upload failed!")
            for err in result.get('errors', []):
                print(f"   • {err}")
    
    # Validate command
    elif args.command == 'validate':
        if not Path(args.file).exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        
        result = system.validate_upload(args.file, args.purpose)
        
        print(f"\n📋 Validation Results for: {Path(args.file).name}")
        print(f"   Purpose: {args.purpose}")
        print(f"   Valid: {'✅ Yes' if result['valid'] else '❌ No'}")
        
        if result.get('errors'):
            print(f"\n   Errors ({len(result['errors'])}):")
            for err in result['errors'][:10]:
                print(f"      • {err}")
        
        if result.get('warnings'):
            print(f"\n   Warnings ({len(result['warnings'])}):")
            for warn in result['warnings'][:5]:
                print(f"      • {warn}")
    
    # List commands
    elif args.command == 'list-reports':
        reports = system.list_reports()
        print("\n📊 Available Reports:")
        print("=" * 60)
        for r in reports:
            print(f"\n  {r['id']}")
            print(f"    {r['name']}")
            print(f"    {r['description']}")
            if r['available_filters']:
                print(f"    Filters: {', '.join(r['available_filters'])}")
    
    elif args.command == 'list-templates':
        templates = system.list_templates()
        print("\n📋 Available Templates:")
        print("=" * 60)
        for t in templates:
            print(f"\n  {t['name']}")
            print(f"    {t['display_name']}")
            print(f"    {t['description']}")
            print(f"    Sheets: {t['sheets']}")
            if t['requires_approval']:
                print("    ⚠️ Requires approval")
    
    elif args.command == 'list-databases':
        databases = system.list_databases()
        print("\n🗄️ Available Databases:")
        print("=" * 60)
        for db in databases:
            env_icon = "🔵" if db['environment'] == 'staging' else "🟢" if db['environment'] == 'production' else "⚪"
            print(f"\n  {env_icon} {db['name']}")
            print(f"    Project: {db['project']}")
            print(f"    Environment: {db['environment']}")
            print(f"    Host: {db['host']}")
    
    # Utility commands
    elif args.command == 'test-connection':
        result = system.test_connection(args.db)
        if result['success']:
            print(f"\n✅ {result['message']}")
        else:
            print(f"\n❌ {result['message']}")
    
    elif args.command == 'info':
        info = system.get_system_info()
        print("\n" + "=" * 60)
        print("SYSTEM INFORMATION")
        print("=" * 60)
        print(f"\nVersion: {info['version']}")
        print(f"\n📊 Reports Available: {len(info['available_reports'])}")
        print(f"📋 Templates Available: {len(info['available_templates'])}")
        print(f"🗄️ Databases Available: {info['available_databases']}")
        print(f"\n📁 Output Directories:")
        for name, path in info['output_directories'].items():
            print(f"   • {name}: {path}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()