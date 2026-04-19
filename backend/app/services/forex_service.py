"""
Forex Service for fetching exchange rates.
"""

import time
import logging
from decimal import Decimal
import httpx

logger = logging.getLogger(__name__)

class ForexService:
    _cache = {}
    _CACHE_TTL = 15 * 60  # 15 minutes in seconds

    @classmethod
    async def get_usd_to_zar(cls) -> Decimal:
        """
        Fetch the live USD to ZAR exchange rate.
        Caches the result to avoid rate-limiting.
        Fallback to 18.50 if API fails.
        """
        now = time.time()
        cached = cls._cache.get("usd_zar_rate")
        
        if cached and (now - cached["timestamp"] < cls._CACHE_TTL):
            return cached["value"]

        # Proceed to fetch from API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://api.frankfurter.dev/v1/latest?from=USD&to=ZAR")
                response.raise_for_status()
                data = response.json()
                rate = Decimal(str(data["rates"]["ZAR"]))
                
                # Cache the successful rate
                cls._cache["usd_zar_rate"] = {
                    "value": rate,
                    "timestamp": now
                }
                return rate
        except Exception as e:
            logger.warning("Failed to fetch USD/ZAR rate from Frankfurter API: %s. Using fallback.", str(e))
            if cached:
                # If we have an expired cache, we might prefer it over static fallback, but per instructions:
                # Fall back to 18.50 if the API is unreachable (could also mean first time).
                pass
            return Decimal("18.50")

    @classmethod
    async def convert_usd_to_zar(cls, usd_amount: Decimal) -> Decimal:
        """Convert a USD amount to ZAR."""
        rate = await cls.get_usd_to_zar()
        return (usd_amount * rate).quantize(Decimal("1.00"))

    @classmethod
    async def convert_zar_to_usd(cls, zar_amount: Decimal) -> Decimal:
        """Convert a ZAR amount to USD."""
        rate = await cls.get_usd_to_zar()
        return (zar_amount / rate).quantize(Decimal("1.00000000"))
