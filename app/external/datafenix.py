import httpx
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

class DataFenixClient:
    """
    Client for DataFenix Menstrual Cycle Analysis (via RapidAPI).
    Includes a local fallback implementation.
    """
    BASE_URL = "https://womens-health-menstrual-cycle.p.rapidapi.com/"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DATAFENIX_API_KEY")
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "womens-health-menstrual-cycle.p.rapidapi.com"
        } if self.api_key else {}

    async def analyze_cycle(self, period_history: List[str]) -> Dict[str, Any]:
        """
        Main entry point: uses API if key exists, otherwise local fallback.
        period_history: List of ISO date strings for period start dates.
        """
        if self.api_key:
            try:
                return await self._call_api(period_history)
            except Exception as e:
                logger.error(f"DataFenix API failed, falling back: {e}")
                return self._local_fallback(period_history)
        else:
            return self._local_fallback(period_history)

    async def _call_api(self, period_history: List[str]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}analyze",
                json={"dates": period_history},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    def _local_fallback(self, period_history: List[str]) -> Dict[str, Any]:
        """
        Stateless local computation of cycle metrics.
        """
        if not period_history:
            return {"status": "insufficient_data"}

        # Sort dates
        dates = sorted([datetime.fromisoformat(d) for d in period_history])
        if len(dates) < 2:
            return {"status": "insufficient_data", "note": "Need at least 2 periods for analysis"}

        # Calculate cycle lengths
        lengths = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
        avg_cycle = np.mean(lengths)
        cv_cycle = np.std(lengths) / avg_cycle if avg_cycle > 0 else 0
        
        last_start = dates[-1]
        today = datetime.now()
        day_in_cycle = (today - last_start).days + 1
        
        # Phase prediction (Approximate)
        # Menstrual: 1-5, Follicular: 6-13, Ovulatory: 14, Luteal: 15-28
        phase = "unknown"
        if 1 <= day_in_cycle <= 5: phase = "Menstrual"
        elif 6 <= day_in_cycle <= 13: phase = "Follicular"
        elif day_in_cycle == 14: phase = "Ovulatory"
        elif 15 <= day_in_cycle <= avg_cycle: phase = "Luteal"
        else: phase = "Late/Prolonged"

        next_period = last_start + timedelta(days=int(avg_cycle))
        
        return {
            "status": "success",
            "source": "local_fallback",
            "metrics": {
                "average_cycle_length": float(avg_cycle),
                "regularity_score": 1.0 - cv_cycle,
                "is_regular": cv_cycle < 0.2 and 21 <= avg_cycle <= 35
            },
            "current_state": {
                "day_in_cycle": day_in_cycle,
                "phase": phase,
                "predicted_next_period": next_period.isoformat()
            }
        }
