"""
Database Configuration Management - Local databases only
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv('config/passwords.env')


class DatabaseType(Enum):
    POSTGRESQL = "postgresql"


@dataclass
class DatabaseConfig:
    name: str
    db_type: DatabaseType
    host: str
    port: int
    database: str
    user: str
    password: str
    ssl_mode: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = None
    project: Optional[str] = None
    
    def get_connection_params(self) -> dict:
        params = {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password,
        }
        if self.ssl_mode:
            params['sslmode'] = self.ssl_mode
        return params


class DatabaseConfigManager:
    def __init__(self):
        self.databases: Dict[str, DatabaseConfig] = {}
        self.load_configs()
    
    def load_configs(self):
        # AG Development (Local)
        self.databases['AG_Dev'] = DatabaseConfig(
            name='AG_Dev',
            db_type=DatabaseType.POSTGRESQL,
            host=os.getenv('AG_DEV_HOST', 'localhost'),
            port=int(os.getenv('AG_DEV_PORT', '5432')),
            database=os.getenv('AG_DEV_DATABASE', 'AG_Dev'),
            user=os.getenv('AG_DEV_USER', 'postgres'),
            password=os.getenv('AG_DEV_PASSWORD', 'postgres'),
            ssl_mode='disable',
            description='Local AG Development Database',
            environment='development',
            project='AG'
        )
        
        # Telios LMS Survey Development (Local)
        self.databases['Telios_LMS_Dev'] = DatabaseConfig(
            name='Telios_LMS_Dev',
            db_type=DatabaseType.POSTGRESQL,
            host=os.getenv('TELIOS_LMS_DEV_HOST', 'localhost'),
            port=int(os.getenv('TELIOS_LMS_DEV_PORT', '5432')),
            database=os.getenv('TELIOS_LMS_DEV_DATABASE', 'LMS_Survey_Dev'),
            user=os.getenv('TELIOS_LMS_DEV_USER', 'postgres'),
            password=os.getenv('TELIOS_LMS_DEV_PASSWORD', 'postgres'),
            ssl_mode='disable',
            description='Local Telios LMS Survey Development Database',
            environment='development',
            project='Telios_LMS'
        )

        self._load_system_database_metadata()

    def _load_system_database_metadata(self):
        """Apply database metadata from system_config.yaml."""
        config_path = Path('config/system_config.yaml')
        if not config_path.exists():
            return

        with config_path.open('r', encoding='utf-8') as f:
            system_config = yaml.safe_load(f) or {}

        database_items = system_config.get('databases', {}).get('items', {})
        for db_name, db_info in database_items.items():
            project = db_info.get('project')
            category = db_info.get('category') or project

            if db_name in self.databases:
                if project:
                    self.databases[db_name].project = project
                if category:
                    self.databases[db_name].description = self.databases[db_name].description or f"{category} Database"
                continue

            env_prefix = db_name.upper()
            self.databases[db_name] = DatabaseConfig(
                name=db_name,
                db_type=DatabaseType.POSTGRESQL,
                host=os.getenv(f'{env_prefix}_HOST', 'localhost'),
                port=int(os.getenv(f'{env_prefix}_PORT', '5432')),
                database=os.getenv(f'{env_prefix}_DATABASE', db_name),
                user=os.getenv(f'{env_prefix}_USER', 'postgres'),
                password=os.getenv(f'{env_prefix}_PASSWORD', 'postgres'),
                ssl_mode='disable',
                description=f"{category or project or db_name} Database",
                environment='development',
                project=project or category
            )
    
    def get_config(self, db_name: str) -> Optional[DatabaseConfig]:
        return self.databases.get(db_name)
    
    def list_databases(self) -> list:
        return list(self.databases.keys())
    
    def get_database_info(self, db_name: str) -> Dict[str, Any]:
        config = self.get_config(db_name)
        if not config:
            return {}
        return {
            'name': config.name,
            'type': config.db_type.value,
            'host': config.host,
            'port': config.port,
            'database': config.database,
            'description': config.description,
            'environment': config.environment,
            'project': config.project,
        }
