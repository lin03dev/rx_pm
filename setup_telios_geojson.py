#!/usr/bin/env python3
"""
Setup Telios GeoJSON tables in the database
"""

import sys
sys.path.insert(0, '.')

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager

def setup_telios_geojson_tables():
    """Create Telios GeoJSON tables if they don't exist"""
    
    db_config = DatabaseConfigManager()
    db_manager = DatabaseManager(db_config)
    db_manager.current_db = 'AG_Dev'  # or Telios_LMS_Dev
    
    # Create teliosgeojson table
    create_teliosgeojson = """
    CREATE TABLE IF NOT EXISTS teliosgeojson (
        id SERIAL PRIMARY KEY,
        feature_id VARCHAR(100) UNIQUE,
        region VARCHAR(100),
        country VARCHAR(100),
        geometry GEOMETRY,
        properties JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_teliosgeojson_region ON teliosgeojson(region);
    CREATE INDEX IF NOT EXISTS idx_teliosgeojson_country ON teliosgeojson(country);
    CREATE INDEX IF NOT EXISTS idx_teliosgeojson_geometry ON teliosgeojson USING GIST(geometry);
    """
    
    # Create teliogeojsondata table
    create_teliogeojsondata = """
    CREATE TABLE IF NOT EXISTS teliogeojsondata (
        id SERIAL PRIMARY KEY,
        geojson_id INTEGER REFERENCES teliosgeojson(id) ON DELETE CASCADE,
        attribute_name VARCHAR(100),
        attribute_value TEXT,
        data_type VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_teliogeojsondata_geojson_id ON teliogeojsondata(geojson_id);
    CREATE INDEX IF NOT EXISTS idx_teliogeojsondata_attribute ON teliogeojsondata(attribute_name);
    """
    
    # Enable PostGIS extension if not already enabled
    enable_postgis = "CREATE EXTENSION IF NOT EXISTS postgis;"
    
    try:
        print("Enabling PostGIS extension...")
        db_manager.execute_update(enable_postgis)
        print("✅ PostGIS extension enabled")
        
        print("\nCreating teliosgeojson table...")
        db_manager.execute_update(create_teliosgeojson)
        print("✅ teliosgeojson table created")
        
        print("\nCreating teliogeojsondata table...")
        db_manager.execute_update(create_teliogeojsondata)
        print("✅ teliogeojsondata table created")
        
        print("\n✅ Telios GeoJSON tables setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nNote: PostGIS extension may need to be installed first.")
        print("Run: sudo apt install postgis postgresql-postgis")

if __name__ == '__main__':
    setup_telios_geojson_tables()
