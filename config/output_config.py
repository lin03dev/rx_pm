"""Output configuration backed by config/system_config.yaml."""

from pathlib import Path
from typing import Dict, Any

import yaml


class OutputConfig:
    """Configuration for output segregation"""
    
    def __init__(self, config_file: str = "config/system_config.yaml"):
        self.config_file = Path(config_file)
        self.mappings = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load output/database mappings from YAML."""
        if self.config_file.exists():
            with self.config_file.open('r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            return self._from_system_config(config)
        return self._get_default_config()

    def _from_system_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize system_config.yaml into the legacy mapping shape."""
        output_config = config.get("output", {})
        categories_config = output_config.get("categories", {})
        databases_config = config.get("databases", {})
        database_items = databases_config.get("items", {})

        # Backward compatibility with the previous system_config shape.
        if not database_items:
            database_items = {
                key: value for key, value in databases_config.items()
                if isinstance(value, dict)
            }

        database_mappings = {}
        report_categories = {}

        for category, paths in categories_config.items():
            report_categories[category] = {
                "databases": [],
                "reports_path": paths.get("reports_path"),
                "templates_path": paths.get("templates_path"),
            }

        for db_name, db_info in database_items.items():
            output_category = db_info.get("output_category") or db_info.get("output_dir") or db_info.get("category") or db_info.get("project") or "AG"
            template_category = db_info.get("template_category") or db_info.get("templates_dir") or output_category
            project_type = db_info.get("project") or db_info.get("category") or output_category

            database_mappings[db_name] = {
                "project_type": project_type,
                "output_folder": output_category,
                "template_folder": template_category,
            }

            report_categories.setdefault(output_category, {
                "databases": [],
                "reports_path": categories_config.get(output_category, {}).get("reports_path"),
                "templates_path": categories_config.get(output_category, {}).get("templates_path"),
            })
            report_categories[output_category].setdefault("databases", []).append(db_name)

        return {
            "default_database": databases_config.get("default", "AG_Dev"),
            "reports_path": output_config.get("reports_path", "./output/reports"),
            "templates_path": output_config.get("templates_path", "./output/templates"),
            "timestamp_format": output_config.get("timestamp_format", "%Y%m%d_%H%M%S"),
            "database_mappings": database_mappings,
            "report_categories": report_categories,
        }
    
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
        """Persisting normalized output mappings is intentionally unsupported."""
        raise NotImplementedError("Edit config/system_config.yaml instead")
    
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

    def get_output_path(self, database_name: str) -> str:
        """Get report output path for a database."""
        category = self.get_output_folder(database_name)
        category_info = self.get_category_info(category)
        return category_info.get("reports_path") or str(Path(self.mappings.get("reports_path", "./output/reports")) / category)

    def get_template_path(self, database_name: str) -> str:
        """Get template output path for a database."""
        category = self.get_template_folder(database_name)
        category_info = self.get_category_info(category)
        return category_info.get("templates_path") or str(Path(self.mappings.get("templates_path", "./output/templates")) / category)
    
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
        """Add a new database mapping in memory."""
        template_folder = template_folder or output_folder
        self.mappings.setdefault("database_mappings", {})[database_name] = {
            "project_type": project_type,
            "output_folder": output_folder,
            "template_folder": template_folder,
        }
        category = self.mappings.setdefault("report_categories", {}).setdefault(output_folder, {"databases": []})
        category.setdefault("databases", [])
        if database_name not in category["databases"]:
            category["databases"].append(database_name)


# Singleton instance
_output_config = None

def get_output_config() -> OutputConfig:
    """Get singleton instance"""
    global _output_config
    if _output_config is None:
        _output_config = OutputConfig()
    return _output_config
