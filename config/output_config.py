"""
Output Configuration - Dynamic mapping of databases to output folders
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class OutputConfig:
    """Configuration for output segregation"""
    
    def __init__(self, config_file: str = "config/database_mappings.json"):
        self.config_file = Path(config_file)
        self.mappings = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "database_mappings": {
                "AG_Dev": {"project_type": "AG", "output_folder": "AG", "template_folder": "AG"},
                "Telios_LMS_Dev": {"project_type": "LMS", "output_folder": "LMS", "template_folder": "LMS"},
                "Telios_Survey_Dev": {"project_type": "Survey", "output_folder": "Telios", "template_folder": "Telios"}
            },
            "report_categories": {
                "AG": {"databases": ["AG_Dev"]},
                "LMS": {"databases": ["Telios_LMS_Dev"]},
                "Survey": {"databases": ["Telios_Survey_Dev"]},
                "Language": {"databases": []}
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.mappings, f, indent=2)
    
    def get_output_folder(self, database_name: str) -> str:
        """Get output folder for a database"""
        db_mapping = self.mappings.get("database_mappings", {}).get(database_name, {})
        return db_mapping.get("output_folder", "AG")
    
    def get_template_folder(self, database_name: str) -> str:
        """Get template folder for a database"""
        db_mapping = self.mappings.get("database_mappings", {}).get(database_name, {})
        return db_mapping.get("template_folder", "AG")
    
    def get_project_type(self, database_name: str) -> str:
        """Get project type for a database"""
        db_mapping = self.mappings.get("database_mappings", {}).get(database_name, {})
        return db_mapping.get("project_type", "AG")
    
    def get_category_info(self, category: str) -> Dict[str, Any]:
        """Get information about a category"""
        return self.mappings.get("report_categories", {}).get(category, {})
    
    def get_database_category(self, database_name: str) -> str:
        """Get which category a database belongs to"""
        for category, info in self.mappings.get("report_categories", {}).items():
            if database_name in info.get("databases", []):
                return category
        return "AG"
    
    def list_categories(self) -> list:
        """List all available categories"""
        return list(self.mappings.get("report_categories", {}).keys())
    
    def list_databases_by_category(self, category: str) -> list:
        """List databases in a category"""
        info = self.get_category_info(category)
        return info.get("databases", [])
    
    def get_reports_for_category(self, category: str) -> list:
        """Get reports for a category"""
        info = self.get_category_info(category)
        return info.get("reports", [])
    
    def get_templates_for_category(self, category: str) -> list:
        """Get templates for a category"""
        info = self.get_category_info(category)
        return info.get("templates", [])
    
    def add_database_mapping(self, database_name: str, project_type: str, 
                            output_folder: str, template_folder: str = None):
        """Add a new database mapping"""
        if template_folder is None:
            template_folder = output_folder
        
        if "database_mappings" not in self.mappings:
            self.mappings["database_mappings"] = {}
        
        self.mappings["database_mappings"][database_name] = {
            "project_type": project_type,
            "output_folder": output_folder,
            "template_folder": template_folder
        }
        
        # Also add to category
        if project_type not in self.mappings.get("report_categories", {}):
            self.mappings.setdefault("report_categories", {})[project_type] = {"databases": []}
        
        if database_name not in self.mappings["report_categories"][project_type]["databases"]:
            self.mappings["report_categories"][project_type]["databases"].append(database_name)
        
        self.save_config()


# Singleton instance
_output_config = None

def get_output_config() -> OutputConfig:
    """Get singleton instance"""
    global _output_config
    if _output_config is None:
        _output_config = OutputConfig()
    return _output_config
