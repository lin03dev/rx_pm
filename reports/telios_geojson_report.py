"""
Telios GeoJSON Report - Comprehensive reporting for geographic data
"""

import pandas as pd
import json
from typing import Dict, Any, List
from pathlib import Path

from reports.base_report_v2 import BaseReportV2


class TeliosGeoJSONReport(BaseReportV2):
    """
    Telios GeoJSON Report - Analyze geographic data from teliosgeojson and teliogeojsondata
    """
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['region', 'country', 'project_type', 'date_range']
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate comprehensive Telios GeoJSON report"""
        
        results = {}
        
        # 1. GEOJSON DATA OVERVIEW
        results['geojson_overview'] = self._get_geojson_overview()
        
        # 2. SPATIAL DISTRIBUTION
        results['spatial_distribution'] = self._get_spatial_distribution()
        
        # 3. DATA QUALITY REPORT
        results['data_quality'] = self._get_data_quality()
        
        # 4. GEOJSON VALIDATION
        results['geojson_validation'] = self._validate_geojson()
        
        # 5. PROJECT LOCATIONS
        results['project_locations'] = self._get_project_locations()
        
        # 6. REGION SUMMARY
        results['region_summary'] = self._get_region_summary()
        
        # 7. INTEGRATION WITH LMS
        results['lms_integration'] = self._get_lms_integration()
        
        # 8. SUMMARY STATISTICS
        results['summary_stats'] = self._get_summary_stats(results)
        
        return results
    
    def _get_geojson_overview(self) -> pd.DataFrame:
        """Get overview of GeoJSON data"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT region) as unique_regions,
                COUNT(DISTINCT country) as unique_countries,
                MIN(created_at) as earliest_record,
                MAX(updated_at) as latest_record
            FROM teliosgeojson
            """
            df = self.execute_query(query)
            return df
        except:
            return pd.DataFrame({'Message': ['Telios GeoJSON table not found. Please create the table first.']})
    
    def _get_spatial_distribution(self) -> pd.DataFrame:
        """Get spatial distribution of data"""
        try:
            query = """
            SELECT 
                region,
                country,
                COUNT(*) as feature_count,
                COUNT(DISTINCT project_id) as project_count
            FROM teliosgeojson
            GROUP BY region, country
            ORDER BY feature_count DESC
            """
            df = self.execute_query(query)
            return df
        except:
            return pd.DataFrame({'Message': ['Unable to retrieve spatial distribution']})
    
    def _get_data_quality(self) -> pd.DataFrame:
        """Check data quality of GeoJSON records"""
        try:
            query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN geometry IS NULL THEN 1 ELSE 0 END) as missing_geometry,
                SUM(CASE WHEN properties IS NULL THEN 1 ELSE 0 END) as missing_properties,
                SUM(CASE WHEN ST_IsValid(geometry) = false THEN 1 ELSE 0 END) as invalid_geometry
            FROM teliosgeojson
            """
            df = self.execute_query(query)
            return df
        except:
            return pd.DataFrame({'Message': ['Data quality check not available']})
    
    def _validate_geojson(self) -> pd.DataFrame:
        """Validate GeoJSON format and structure"""
        try:
            query = """
            SELECT 
                id,
                CASE 
                    WHEN geometry IS NULL THEN 'Missing Geometry'
                    WHEN ST_GeometryType(geometry) NOT IN ('ST_Polygon', 'ST_MultiPolygon', 'ST_Point') THEN 'Invalid Geometry Type'
                    ELSE 'Valid'
                END as validation_status
            FROM teliosgeojson
            WHERE geometry IS NOT NULL
            LIMIT 100
            """
            df = self.execute_query(query)
            
            # Add validation summary
            summary = df['validation_status'].value_counts().reset_index()
            summary.columns = ['Status', 'Count']
            return summary
        except:
            return pd.DataFrame({'Message': ['GeoJSON validation not available']})
    
    def _get_project_locations(self) -> pd.DataFrame:
        """Get project locations mapped to GeoJSON"""
        try:
            query = """
            SELECT 
                p.name as project_name,
                p.project_type,
                l.name as language,
                c.name as country,
                g.region,
                ST_AsGeoJSON(g.geometry) as geojson
            FROM projects p
            LEFT JOIN languages l ON p.language_id = l.id
            LEFT JOIN countries c ON p.country_id = c.id
            LEFT JOIN teliosgeojson g ON c.name = g.country
            WHERE g.id IS NOT NULL
            ORDER BY c.name, p.name
            """
            df = self.execute_query(query)
            return df
        except:
            return pd.DataFrame({'Message': ['Unable to map project locations']})
    
    def _get_region_summary(self) -> pd.DataFrame:
        """Get summary by region"""
        try:
            query = """
            SELECT 
                region,
                COUNT(*) as feature_count,
                COUNT(DISTINCT country) as country_count,
                MIN(created_at) as first_record,
                MAX(updated_at) as last_record
            FROM teliosgeojson
            GROUP BY region
            ORDER BY feature_count DESC
            """
            df = self.execute_query(query)
            return df
        except:
            return pd.DataFrame({'Message': ['Region summary not available']})
    
    def _get_lms_integration(self) -> pd.DataFrame:
        """Integrate GeoJSON data with LMS tables"""
        try:
            query = """
            SELECT 
                g.region,
                g.country,
                COUNT(DISTINCT b.id) as batch_count,
                COUNT(DISTINCT e.id) as enrollment_count,
                COUNT(DISTINCT p.id) as project_count
            FROM teliosgeojson g
            LEFT JOIN countries c ON g.country = c.name
            LEFT JOIN projects p ON c.id = p.country_id
            LEFT JOIN batch b ON p.id = b.course_id
            LEFT JOIN enrollment e ON b.id = e.batch
            GROUP BY g.region, g.country
            ORDER BY batch_count DESC, enrollment_count DESC
            """
            df = self.execute_query(query)
            return df
        except:
            return pd.DataFrame({'Message': ['LMS integration not available']})
    
    def _get_summary_stats(self, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Generate summary statistics"""
        stats = []
        
        if 'geojson_overview' in results and not results['geojson_overview'].empty:
            df = results['geojson_overview']
            if 'total_records' in df.columns:
                stats.append({'Metric': 'Total GeoJSON Records', 'Value': df['total_records'].iloc[0]})
            if 'unique_regions' in df.columns:
                stats.append({'Metric': 'Unique Regions', 'Value': df['unique_regions'].iloc[0]})
            if 'unique_countries' in df.columns:
                stats.append({'Metric': 'Unique Countries', 'Value': df['unique_countries'].iloc[0]})
        
        if 'spatial_distribution' in results and not results['spatial_distribution'].empty:
            df = results['spatial_distribution']
            stats.append({'Metric': 'Regions with Data', 'Value': df['region'].nunique()})
        
        if 'region_summary' in results and not results['region_summary'].empty:
            df = results['region_summary']
            stats.append({'Metric': 'Total Regions', 'Value': len(df)})
            stats.append({'Metric': 'Most Features in Region', 'Value': df.iloc[0]['region'] if not df.empty else 'N/A'})
        
        if not stats:
            stats = [{'Metric': 'Status', 'Value': 'No Telios GeoJSON data available'}]
        
        return pd.DataFrame(stats)
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'geojson_overview': '1. GeoJSON Overview',
            'spatial_distribution': '2. Spatial Distribution',
            'data_quality': '3. Data Quality',
            'geojson_validation': '4. GeoJSON Validation',
            'project_locations': '5. Project Locations',
            'region_summary': '6. Region Summary',
            'lms_integration': '7. LMS Integration',
            'summary_stats': '8. Summary Statistics'
        }


class TeliosGeoJSONDataReport(BaseReportV2):
    """
    Detailed Telios GeoJSON Data Report
    """
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['feature_id', 'region', 'country']
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        results = {}
        
        # Get all features
        results['features'] = self._get_all_features()
        
        # Get feature attributes
        results['feature_attributes'] = self._get_feature_attributes()
        
        # Get geometry summary
        results['geometry_summary'] = self._get_geometry_summary()
        
        return results
    
    def _get_all_features(self) -> pd.DataFrame:
        try:
            query = """
            SELECT 
                id,
                feature_id,
                region,
                country,
                ST_AsGeoJSON(geometry) as geometry,
                properties,
                created_at,
                updated_at
            FROM teliosgeojson
            ORDER BY region, country
            """
            df = self.execute_query(query)
            return df
        except:
            return pd.DataFrame({'Message': ['Unable to retrieve features']})
    
    def _get_feature_attributes(self) -> pd.DataFrame:
        try:
            query = """
            SELECT 
                t.id,
                t.feature_id,
                d.attribute_name,
                d.attribute_value,
                d.data_type
            FROM teliosgeojson t
            LEFT JOIN teliogeojsondata d ON t.id = d.geojson_id
            ORDER BY t.id, d.attribute_name
            """
            df = self.execute_query(query)
            return df
        except:
            return pd.DataFrame({'Message': ['Unable to retrieve feature attributes']})
    
    def _get_geometry_summary(self) -> pd.DataFrame:
        try:
            query = """
            SELECT 
                ST_GeometryType(geometry) as geometry_type,
                COUNT(*) as count,
                ST_Area(ST_Collect(geometry)) as total_area,
                ST_AsGeoJSON(ST_Extent(geometry)) as bounding_box
            FROM teliosgeojson
            WHERE geometry IS NOT NULL
            GROUP BY ST_GeometryType(geometry)
            """
            df = self.execute_query(query)
            return df
        except:
            return pd.DataFrame({'Message': ['Unable to summarize geometry']})
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'features': '1. All Features',
            'feature_attributes': '2. Feature Attributes',
            'geometry_summary': '3. Geometry Summary'
        }
