"""
Report Engine - Core reporting engine that orchestrates report generation
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Type
from datetime import datetime
import logging
import json
from pathlib import Path

from core.database_manager import DatabaseManager
from config.output_config import get_output_config
from reports.base_report import BaseReport
from utils.excel_formatter import ExcelFormatter
from utils.report_excel_writer import get_report_excel_writer
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ReportEngine:
    """Main reporting engine"""
    
    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        self.db_manager = db_manager
        self.config = config
        self.reports = {}
        self.report_instances = {}
        output_config = config.get('output', {})
        self.output_path = output_config.get('reports_path') or output_config.get('default_path', './output/reports')
        
        # Create output directory
        Path(self.output_path).mkdir(parents=True, exist_ok=True)
        
    def register_report(self, name: str, report_class: Type[BaseReport]):
        """Register a report type"""
        self.reports[name] = report_class
        logger.info(f"Registered report: {name}")
    
    def get_report(self, report_name: str, **kwargs) -> BaseReport:
        """Get or create a report instance"""
        if report_name not in self.reports:
            raise ValueError(f"Report not found: {report_name}")
        
        report_class = self.reports[report_name]
        report = report_class(self.db_manager, **kwargs)
        self.report_instances[report_name] = report
        return report
    
    def generate_report(self, report_name: str, 
                       output_format: str = 'excel',
                       filters: Optional[Dict] = None,
                       db_name: Optional[str] = None,
                       **kwargs) -> str:
        """Generate a report"""
        report = self.get_report(
            report_name,
            db_name=db_name,
            report_id=report_name,
            **kwargs,
        )
        
        if filters:
            report.apply_filters(filters)
        
        data = report.generate()

        from config.report_schema import apply_schema_output, resolve_sheet_names, validate_report_output
        data = apply_schema_output(report_name, data)
        sheet_names = resolve_sheet_names(report_name, report.get_sheet_names())

        if output_format == 'excel':
            try:
                for issue in validate_report_output(report_name, data):
                    logger.warning("Report output schema mismatch: %s", issue)
            except Exception:
                pass

        output_file = self._get_output_filename(report_name, output_format, db_name=db_name)
        
        if output_format == 'excel':
            self._save_as_excel(data, output_file, sheet_names, report_name=report_name)
        elif output_format == 'csv':
            self._save_as_csv(data, output_file)
        elif output_format == 'json':
            self._save_as_json(data, output_file)
        
        logger.info(f"Report generated: {output_file}")
        return output_file
    
    def generate_custom_report(self, query: str, 
                              report_name: str = "custom",
                              output_format: str = 'excel',
                              params: Optional[Dict] = None,
                              db_name: Optional[str] = None) -> str:
        """Generate a custom report from raw SQL"""
        try:
            data = self.db_manager.execute_query(query, params, db_name=db_name)
        except Exception as e:
            data = pd.DataFrame({'Error': [str(e)], 'Query': [query[:500]]})
        
        output_file = self._get_output_filename(report_name, output_format, db_name=db_name)
        
        if output_format == 'excel':
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                data.to_excel(writer, sheet_name='Data', index=False)
                if 'Data' in writer.sheets:
                    ExcelFormatter.format_worksheet(writer.sheets['Data'])
        elif output_format == 'csv':
            data.to_csv(output_file, index=False)
        elif output_format == 'json':
            data.to_json(output_file, orient='records', indent=2)
        
        logger.info(f"Custom report generated: {output_file}")
        return output_file
    
    def _get_output_filename(self, report_name: str, format_type: str, db_name: Optional[str] = None) -> str:
        """Generate output filename with timestamp"""
        extension_map = {'excel': 'xlsx', 'csv': 'csv', 'json': 'json'}
        extension = extension_map.get(format_type, 'xlsx')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = report_name.replace(' ', '_').lower()
        filename = f"{clean_name}_{timestamp}.{extension}"
        output_path = get_output_config().get_output_path(db_name) if db_name else self.output_path
        Path(output_path).mkdir(parents=True, exist_ok=True)
        return str((Path(output_path) / filename).resolve())
    
    def _save_as_excel(self, data: Dict[str, pd.DataFrame], 
                      filename: str, sheet_names: Dict[str, str],
                      report_name: Optional[str] = None):
        """Save data as Excel with template-driven formatting when configured."""
        writer = get_report_excel_writer()
        writer.save_report(
            output_path=filename,
            report_data=data,
            sheet_names=sheet_names,
            report_id=report_name,
        )
    
    def _save_as_csv(self, data: Dict[str, pd.DataFrame], filename: str):
        """Save data as CSV (first sheet only)"""
        first_key = list(data.keys())[0]
        data[first_key].to_csv(filename, index=False)
    
    def _save_as_json(self, data: Dict[str, pd.DataFrame], filename: str):
        """Save data as JSON"""
        result = {}
        for key, df in data.items():
            result[key] = df.to_dict(orient='records')
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
    
    def list_available_reports(self) -> List[str]:
        """List all registered reports"""
        return list(self.reports.keys())
