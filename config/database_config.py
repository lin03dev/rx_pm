"""
Database Configuration Management - Local databases only
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
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
            host='localhost',
            port=5432,
            database='AG_Dev',
            user='postgres',
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
            host='localhost',
            port=5432,
            database='Telios_LMS_Survey_Dev',
            user='postgres',
            password=os.getenv('TELIOS_LMS_DEV_PASSWORD', 'postgres'),
            ssl_mode='disable',
            description='Local Telios LMS Survey Development Database',
            environment='development',
            project='Telios_LMS'
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
