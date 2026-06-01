#!/usr/bin/env python3
"""Preflight local database connections for the reporting pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager


def main():
    config_manager = DatabaseConfigManager()
    db_manager = DatabaseManager(config_manager)
    connected = []

    for alias in config_manager.list_databases():
        config = config_manager.get_config(alias)
        try:
            conn = db_manager._get_connection(alias)
            connected.append(f"{alias}->{config.database}")
            conn.close()
            db_manager.connections.pop(alias, None)
        except Exception as exc:
            print(
                f"Local database preflight failed for {alias}->{config.database} "
                f"at {config.host}:{config.port}: {exc}"
            )
            return 1

    print("Local database preflight OK: " + ", ".join(connected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
