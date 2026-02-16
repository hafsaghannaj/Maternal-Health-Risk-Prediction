import httpx
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import asyncio

logger = logging.getLogger(__name__)

# Pydantic Models for Type Safety
class MeasureMetadata(BaseModel):
    name: str
    description: Optional[str] = None
    source: Optional[str] = None
    units: Optional[str] = None

class Subpopulation(BaseModel):
    name: str
    populationCategory: Optional[Dict[str, str]] = None

class AHRDataPoint(BaseModel):
    state: str
    value: Optional[float] = None
    year: Optional[int] = None
    measure: MeasureMetadata
    subpopulation: Optional[Subpopulation] = None
    edition: Optional[str] = None

class AHRClient:
    """
    Async GraphQL client for America's Health Rankings API.
    """
    BASE_URL = "https://api.americashealthrankings.org/graphql"

    def __init__(self, redis_client=None):
        self.redis = redis_client

    async def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None, dataset: str = "data_A") -> List[AHRDataPoint]:
        cache_key = f"ahr:{dataset}:{hash(query + str(variables))}"
        
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                return [AHRDataPoint(**item) for item in data]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.BASE_URL,
                json={"query": query, "variables": variables},
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"AHR API Error: {response.status_code} - {response.text}")
                response.raise_for_status()

            payload = response.json()
            if "errors" in payload:
                logger.error(f"GraphQL Errors: {payload['errors']}")
                raise Exception(f"GraphQL Error: {payload['errors'][0]['message']}")

            # Extract data from the requested dataset field
            data_list = payload.get("data", {}).get(dataset, [])
            results = [AHRDataPoint(**item) for item in data_list]

            if self.redis and results:
                await self.redis.setex(cache_key, 604800, json.dumps([r.dict() for r in results])) # 1-week TTL
                
            return results

    async def get_measure_by_state(self, measure_name: str, year: Optional[int] = None) -> List[AHRDataPoint]:
        query = """
        query($name: String!) {
          data_A(where: { measure: { name: { eq: $name } } }) {
            state
            value
            year
            edition
            measure {
              name
              description
            }
          }
        }
        """
        return await self._execute_query(query, {"name": measure_name})

    async def get_measure_with_disparities(self, measure_name: str) -> List[AHRDataPoint]:
        query = """
        query($name: String!) {
          data_B(where: { measure: { name: { eq: $name } } }) {
            state
            value
            year
            subpopulation {
              name
              populationCategory {
                name
              }
            }
            measure {
              name
              description
            }
          }
        }
        """
        return await self._execute_query(query, {"name": measure_name}, dataset="data_B")

    async def get_state_profile(self, state_abbr: str) -> List[AHRDataPoint]:
        query = """
        query($state: String!) {
          data_A(where: { state: { eq: $state } }) {
            state
            value
            year
            measure {
              name
              description
            }
          }
        }
        """
        return await self._execute_query(query, {"state": state_abbr})

    async def get_maternal_disparity_brief(self) -> List[AHRDataPoint]:
        # Specific query for the Maternal & Infant Health Disparities Data Brief
        # As requested, use data_B which typically holds this stratified data
        query = """
        query {
          data_B(where: { edition: { eq: "2024 Maternal & Infant Health Disparities" } }) {
            state
            value
            year
            subpopulation {
              name
            }
            measure {
              name
            }
          }
        }
        """
        return await self._execute_query(query)

    async def get_rankings(self, report: str = "women_and_children") -> List[AHRDataPoint]:
        # Report mapping logic might be needed here to select the right measure
        query = """
        query {
          data_A(where: { measure: { name: { eq: "Overall Ranking" } } }) {
            state
            value
            year
            measure {
              name
            }
          }
        }
        """
        return await self._execute_query(query)
