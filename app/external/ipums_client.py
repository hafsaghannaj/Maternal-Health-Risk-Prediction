import httpx
import pandas as pd
import asyncio
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class IPUMSClient:
    """
    Client for IPUMS API (NHIS, PMA) for health data extraction.
    """
    BASE_URL = "https://api.ipums.org/extracts/"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("IPUMS_API_KEY")
        self.headers = {"Authorization": self.api_key} if self.api_key else {}

    async def submit_extract(self, collection: str, variables: list, samples: list, description: str):
        """
        Submits an extract request to IPUMS.
        """
        if not self.api_key:
            logger.warning("IPUMS_API_KEY not set. Skipping extract submission.")
            return None

        url = f"{self.BASE_URL}?collection={collection}"
        extract_definition = {
            "description": description,
            "samples": {s: {} for s in samples},
            "variables": {v: {} for v in variables}
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"extract_definition": extract_definition}, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"IPUMS Extract #{data['number']} submitted.")
            return data['number']

    async def wait_for_extract(self, collection: str, extract_number: int, timeout_sec: int = 3600):
        """
        Polls IPUMS until the extract is ready.
        """
        url = f"{self.BASE_URL}{extract_number}?collection={collection}"
        
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout_sec:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                status = response.json().get("status")
                
                if status == "completed":
                    logger.info(f"IPUMS Extract #{extract_number} is ready.")
                    return response.json().get("download_links", {}).get("data")
                elif status == "failed":
                    raise Exception(f"IPUMS Extract #{extract_number} failed.")
                
                logger.info(f"IPUMS Extract #{extract_number} status: {status}. Waiting...")
                await asyncio.sleep(60) # Poll every 60 seconds
                
        raise TimeoutError("IPUMS extract took too long.")

    async def download_and_parse(self, download_url: str):
        """
        Downloads the extract and parses it into a DataFrame.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url, headers=self.headers)
            response.raise_for_status()
            # Note: IPUMS files are often Gzipped .dat or .csv
            # For simplicity, we assume we can read it directly or via pandas
            from io import BytesIO
            import gzip
            content = gzip.decompress(response.content)
            return pd.read_csv(BytesIO(content))
