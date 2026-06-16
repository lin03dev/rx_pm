"""Load system configuration from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SYSTEM_CONFIG = BACKEND_DIR / "config" / "system_config.yaml"


def load_config(config_file: str | Path = DEFAULT_SYSTEM_CONFIG) -> dict:
    """Load configuration from YAML and ensure output directories exist."""
    config_path = Path(config_file)
    default_config = {
        "output": {
            "reports_path": "./output/reports",
            "templates_path": "./output/templates",
            "uploads_path": "./output/uploads",
            "logs_path": "./output/logs",
            "timestamp_format": "%Y%m%d_%H%M%S",
            "categories": {
                "AG": {"reports_path": "./output/reports/AG", "templates_path": "./output/templates/AG"},
                "LMS": {"reports_path": "./output/reports/LMS", "templates_path": "./output/templates/LMS"},
                "Telios": {"reports_path": "./output/reports/Telios", "templates_path": "./output/templates/Telios"},
                "Language": {"reports_path": "./output/reports/Language", "templates_path": "./output/templates/Language"},
            },
        }
    }

    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            user_config = yaml.safe_load(handle) or {}
        for key, value in user_config.items():
            if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                default_config[key].update(value)
            else:
                default_config[key] = value

    output_config = default_config.setdefault("output", {})
    output_config.setdefault("reports_path", output_config.get("default_path", "./output/reports"))
    templates_config = output_config.get("templates") or default_config.get("templates", {})
    output_config.setdefault("templates_path", templates_config.get("default_path", "./output/templates"))
    output_config.setdefault("uploads_path", "./output/uploads")
    output_config.setdefault("logs_path", "./output/logs")

    if "categories" not in output_config:
        report_dirs = output_config.get("subdirectories", {})
        template_dirs = templates_config.get("subdirectories", {})
        output_config["categories"] = {
            category: {
                "reports_path": report_path,
                "templates_path": template_dirs.get(category, str(Path(output_config["templates_path"]) / category)),
            }
            for category, report_path in report_dirs.items()
        }

    for path_key in ["reports_path", "templates_path", "uploads_path", "logs_path"]:
        Path(output_config[path_key]).mkdir(parents=True, exist_ok=True)

    for category in output_config.get("categories", {}).values():
        if category.get("reports_path"):
            Path(category["reports_path"]).mkdir(parents=True, exist_ok=True)
        if category.get("templates_path"):
            Path(category["templates_path"]).mkdir(parents=True, exist_ok=True)

    return default_config
