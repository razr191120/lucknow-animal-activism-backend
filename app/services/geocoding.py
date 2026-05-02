import asyncio
import logging
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GeocodingResult:
    address: str
    latitude: float | None
    longitude: float | None
    display_name: str | None
    success: bool


class GeocodingService:
    """Geocodes addresses using the OpenStreetMap Nominatim API."""

    RATE_LIMIT_SECONDS = 1.1

    def __init__(self) -> None:
        self._cache: dict[str, GeocodingResult] = {}

    def _normalize_query(self, address: str) -> str:
        lower = address.lower().strip()
        if "lucknow" not in lower:
            return f"{address.strip()}, Lucknow, India"
        if "india" not in lower:
            return f"{address.strip()}, India"
        return address.strip()

    async def geocode_single(self, address: str) -> GeocodingResult:
        normalized = self._normalize_query(address)

        if normalized in self._cache:
            return self._cache[normalized]

        params = {
            "q": normalized,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {"User-Agent": settings.NOMINATIM_USER_AGENT}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    settings.NOMINATIM_BASE_URL,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            if data:
                result = GeocodingResult(
                    address=address,
                    latitude=float(data[0]["lat"]),
                    longitude=float(data[0]["lon"]),
                    display_name=data[0].get("display_name"),
                    success=True,
                )
            else:
                result = GeocodingResult(
                    address=address,
                    latitude=None,
                    longitude=None,
                    display_name=None,
                    success=False,
                )
        except Exception:
            logger.exception("Geocoding failed for address: %s", address)
            result = GeocodingResult(
                address=address,
                latitude=None,
                longitude=None,
                display_name=None,
                success=False,
            )

        self._cache[normalized] = result
        return result

    async def geocode_batch(self, addresses: list[str]) -> list[GeocodingResult]:
        results: list[GeocodingResult] = []
        for i, address in enumerate(addresses):
            result = await self.geocode_single(address)
            results.append(result)
            if i < len(addresses) - 1:
                await asyncio.sleep(self.RATE_LIMIT_SECONDS)
        return results


geocoding_service = GeocodingService()
