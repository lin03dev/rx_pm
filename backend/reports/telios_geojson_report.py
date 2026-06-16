"""
Telios GeoJSON Report - aligned with Telios schema (teliosgeojson, teliosgeojsondata, country, language).
"""

from typing import Dict, List, Optional

import pandas as pd

from reports.base_report_v2 import BaseReportV2


class TeliosGeoJSONReport(BaseReportV2):
    """Summary report for Telios geographic survey hierarchy."""

    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)

    def generate(self) -> Dict[str, pd.DataFrame]:
        return {
            "geojson_overview": self._get_geojson_overview(),
            "level_distribution": self._get_level_distribution(),
            "country_summary": self._get_country_summary(),
            "language_summary": self._get_language_summary(),
            "geojson_data": self._get_geojson_data(),
            "summary_stats": self._get_summary_stats(),
        }

    def _table_columns(self, table_name: str) -> List[str]:
        return [name.lower() for name in self.schema.table_columns(table_name)]

    def _table_exists(self, table_name: str) -> bool:
        return self.schema.has_table(table_name)

    def _get_geojson_overview(self) -> pd.DataFrame:
        if not self._table_exists("teliosgeojson"):
            return pd.DataFrame({"Message": ["teliosgeojson table not found"]})

        query = """
        SELECT
            COUNT(*) AS total_units,
            COUNT(DISTINCT tg.country_id) AS countries_covered,
            COUNT(DISTINCT tg.levelkey) AS level_keys,
            COUNT(DISTINCT tg.unitid) AS unit_ids
        FROM teliosgeojson tg
        """
        try:
            return self.execute_query(query)
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]})

    def _get_level_distribution(self) -> pd.DataFrame:
        if not self._table_exists("teliosgeojson"):
            return pd.DataFrame({"Message": ["teliosgeojson table not found"]})

        query = """
        SELECT
            tg.levelkey,
            tg.tellevelkey,
            COUNT(*) AS unit_count,
            COUNT(DISTINCT tg.country_id) AS country_count
        FROM teliosgeojson tg
        GROUP BY tg.levelkey, tg.tellevelkey
        ORDER BY unit_count DESC, tg.levelkey
        """
        try:
            return self.execute_query(query)
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]})

    def _get_country_summary(self) -> pd.DataFrame:
        if not self._table_exists("teliosgeojson"):
            return pd.DataFrame({"Message": ["teliosgeojson table not found"]})

        country_join = ""
        country_select = "tg.country_id::text AS country_id"
        if self._table_exists("country"):
            country_join = "LEFT JOIN country c ON tg.country_id = c.id"
            country_select = "COALESCE(c.country, tg.country_id::text) AS country"

        query = f"""
        SELECT
            {country_select},
            COUNT(*) AS unit_count,
            COUNT(DISTINCT tg.levelkey) AS level_keys
        FROM teliosgeojson tg
        {country_join}
        GROUP BY {country_select.split(' AS ')[0]}
        ORDER BY unit_count DESC
        """
        try:
            return self.execute_query(query)
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]})

    def _get_language_summary(self) -> pd.DataFrame:
        if not self._table_exists("language"):
            return pd.DataFrame({"Message": ["language table not found"]})

        query = """
        SELECT
            l.language_name,
            l.rolv_code,
            l.rolv_name,
            l.iso_code,
            COALESCE(c.country, l.country::text) AS country
        FROM language l
        LEFT JOIN country c ON l.country = c.id
        ORDER BY country, l.language_name
        """
        try:
            return self.execute_query(query)
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]})

    def _get_geojson_data(self) -> pd.DataFrame:
        if not self._table_exists("teliosgeojsondata"):
            return pd.DataFrame({"Message": ["teliosgeojsondata table not found"]})

        query = """
        SELECT
            d.id,
            d.teliosgeojson_id,
            d.levelkey,
            LEFT(d.geojson::text, 500) AS geojson_preview
        FROM teliosgeojsondata d
        ORDER BY d.teliosgeojson_id, d.id
        """
        try:
            return self.execute_query(query)
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]})

    def _get_summary_stats(self) -> pd.DataFrame:
        stats = []
        overview = self._get_geojson_overview()
        if not overview.empty and "total_units" in overview.columns:
            stats.append({"Metric": "Total Geo Units", "Value": int(overview["total_units"].iloc[0])})
        if not overview.empty and "countries_covered" in overview.columns:
            stats.append({"Metric": "Countries Covered", "Value": int(overview["countries_covered"].iloc[0])})

        languages = self._get_language_summary()
        if not languages.empty and "language_name" in languages.columns:
            stats.append({"Metric": "Languages Listed", "Value": int(languages["language_name"].nunique())})

        if not stats:
            stats = [{"Metric": "Status", "Value": "No Telios GeoJSON data available"}]
        return pd.DataFrame(stats)



class TeliosGeoJSONDataReport(BaseReportV2):
    """Detailed Telios GeoJSON export."""

    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)

    def _table_exists(self, table_name: str) -> bool:
        return self.schema.has_table(table_name)

    def generate(self) -> Dict[str, pd.DataFrame]:
        return {
            "geo_units": self._get_geo_units(),
            "geojson_payloads": self._get_geojson_payloads(),
        }

    def _get_geo_units(self) -> pd.DataFrame:
        if not self._table_exists("teliosgeojson"):
            return pd.DataFrame({"Message": ["teliosgeojson table not found"]})

        country_join = ""
        country_select = "tg.country_id::text AS country"
        if self._table_exists("country"):
            country_join = "LEFT JOIN country c ON tg.country_id = c.id"
            country_select = "COALESCE(c.country, tg.country_id::text) AS country"

        query = f"""
        SELECT
            tg.id,
            tg.levelid,
            tg.levelkey,
            tg.unitid,
            tg.tellevelkey,
            tg.countnextlevel,
            tg.parent_id,
            {country_select}
        FROM teliosgeojson tg
        {country_join}
        ORDER BY country, tg.levelkey, tg.unitid
        """
        try:
            return self.execute_query(query)
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]})

    def _get_geojson_payloads(self) -> pd.DataFrame:
        if not self._table_exists("teliosgeojsondata"):
            return pd.DataFrame({"Message": ["teliosgeojsondata table not found"]})

        query = """
        SELECT
            d.id,
            d.teliosgeojson_id,
            d.levelkey,
            d.geojson
        FROM teliosgeojsondata d
        ORDER BY d.teliosgeojson_id, d.id
        """
        try:
            return self.execute_query(query)
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]})

