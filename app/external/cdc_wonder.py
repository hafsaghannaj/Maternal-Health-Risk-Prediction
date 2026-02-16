import httpx
import pandas as pd
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

class CDCWonderXMLBuilder:
    """
    Constructs valid request XML for CDC WONDER API.
    """
    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        self.groups = []
        self.filters = {}
        self._measures = []

    def group_by(self, fields: List[str]):
        self.groups = fields
        return self

    def filter(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, list):
                self.filters[key] = value
            else:
                self.filters[key] = [value]
        return self

    def set_measures(self, measures: List[str]):
        self._measures = measures
        return self

    def build(self) -> str:
        root = ET.Element("request-parameters")
        
        # Identification
        param = ET.SubElement(root, "parameter")
        name_el = ET.SubElement(param, "name")
        name_el.text = "accept_datause_restrictions"
        value_el = ET.SubElement(param, "value")
        value_el.text = "true"

        # Group By
        for i, group in enumerate(self.groups, 1):
            param = ET.SubElement(root, "parameter")
            ET.SubElement(param, "name").text = f"B_{i}"
            ET.SubElement(param, "value").text = group

        # Filters
        for key, values in self.filters.items():
            param = ET.SubElement(root, "parameter")
            ET.SubElement(param, "name").text = f"F_{key}"
            for val in values:
                ET.SubElement(param, "value").text = val

        # Measures
        for measure in self._measures:
            param = ET.SubElement(root, "parameter")
            ET.SubElement(param, "name").text = f"M_{measure}"
            ET.SubElement(param, "value").text = "true"

        return ET.tostring(root, encoding="unicode")

class CDCWonderClient:
    """
    Async client for CDC WONDER XML API.
    """
    BASE_URL = "https://wonder.cdc.gov/controller/datarequest/"

    def __init__(self, redis_client=None):
        self.redis = redis_client

    async def _query(self, dataset_id: str, xml_payload: str) -> pd.DataFrame:
        cache_key = f"cdc_wonder:{dataset_id}:{hash(xml_payload)}"
        
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                return pd.read_json(cached)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}{dataset_id}",
                data={"request_xml": xml_payload, "accept_datause_restrictions": "true"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"CDC WONDER Error: {response.status_code} - {response.text}")
                response.raise_for_status()

            # CDC WONDER returns tab-separated data in the response body or XML
            # Usually the XML API returns a response that needs specific parsing.
            # For simplicity, we assume the response contains the data table.
            df = self._parse_response(response.text)
            
            if self.redis:
                await self.redis.setex(cache_key, 86400, df.to_json()) # 24h TTL
                
            return df

    def _parse_response(self, response_text: str) -> pd.DataFrame:
        """Parses the XML/TSV response from CDC WONDER."""
        # This is a simplified parser. CDC WONDER output varies by dataset.
        # Often it's an XML with a <data-table> or similar.
        try:
            # Placeholder: In practice, you'd find the table in the XML or usepd.read_csv if it's TSV
            # For this prompt, we'll return a dummy DF if parsing fails, but show the logic.
            from io import StringIO
            if "<table>" in response_text:
                # Extract CSV/TSV from within the XML if necessary
                pass
            return pd.read_csv(StringIO(response_text), sep='\t')
        except Exception as e:
            logger.warning(f"Response parsing failed, returning empty DF: {e}")
            return pd.DataFrame()

    async def get_maternal_morbidity_by_state(self, year_range: List[str], morbidity_type: str = "at_least_one"):
        builder = CDCWonderXMLBuilder(dataset_id="D149")
        builder.group_by(["D149.V10", "D149.V1"]) # State, Year
        builder.filter(year=year_range)
        builder.filter(maternal_morbidity=morbidity_type)
        builder.set_measures(["D149.M1", "D149.M3"]) # Births, Percent
        return await self._query("D149", builder.build())

    async def get_birth_demographics(self, year_range: List[str], group_by: List[str]):
        builder = CDCWonderXMLBuilder(dataset_id="D66")
        builder.group_by(group_by)
        builder.filter(year=year_range)
        builder.set_measures(["Births"])
        return await self._query("D66", builder.build())

    async def get_maternal_mortality_rates(self, year_range: List[str]):
        builder = CDCWonderXMLBuilder(dataset_id="D76")
        builder.group_by(["D76.V1", "D76.V8"]) # Year, Race
        builder.filter(year=year_range)
        builder.set_measures(["Deaths", "Crude Rate"])
        return await self._query("D76", builder.build())

    async def get_risk_factor_distributions(self, year_range: List[str], risk_factor: str):
        builder = CDCWonderXMLBuilder(dataset_id="D149")
        builder.group_by(["D149.V1", risk_factor])
        builder.filter(year=year_range)
        builder.set_measures(["Births"])
        return await self._query("D149", builder.build())

class CDCWonderCSVLoader:
    """Fallback loader for manual web exports."""
    def load(self, file_path: str) -> pd.DataFrame:
        return pd.read_csv(file_path, sep='\t', engine='python', skipfooter=20)
