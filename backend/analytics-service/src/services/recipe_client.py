"""
HTTP client for communicating with recipe-service.

Fetches recipe details and ingredient macro data so that
analytics-service can compute nutrition totals server-side.
"""

import logging
from typing import Optional, Dict, Any, List

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)

# Reusable async client — created lazily, closed on shutdown.
_client: Optional[httpx.AsyncClient] = None

# ── Conversion table to grams ──────────────────────────────────────────
# Used when recipe-service stores ingredient quantities in non-gram units.
UNIT_TO_GRAMS: Dict[str, float] = {
    "g": 1.0,
    "kg": 1000.0,
    "ml": 1.0,   
    "l": 1000.0,
    "tsp": 5.0,
    "tbsp": 15.0,
    "cup": 240.0,
    "oz": 28.3495,
    "lb": 453.592,
    "pcs": 100.0,
}


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.RECIPE_SERVICE_URL,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
    return _client


async def close_client() -> None:
    """Gracefully close the HTTP client (call on app shutdown)."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
        logger.info("Recipe-service HTTP client closed")


# ── Public helpers ─────────────────────────────────────────────────────

async def fetch_recipe(recipe_id: str) -> Optional[Dict[str, Any]]:
    """
    GET /recipes/{recipe_id} from recipe-service.
    Returns the raw recipe dict or None on failure.
    """
    client = _get_client()
    try:
        resp = await client.get(f"/recipes/{recipe_id}")
        if resp.status_code == 200:
            return resp.json()
        logger.warning(
            "recipe-service returned %s for recipe %s", resp.status_code, recipe_id
        )
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch recipe %s: %s", recipe_id, exc)
    return None


async def fetch_ingredient(ingredient_id: str) -> Optional[Dict[str, Any]]:
    """
    GET /recipes/ingredients/{ingredient_id} from recipe-service.
    Returns the raw ingredient dict or None on failure.
    """
    client = _get_client()
    try:
        resp = await client.get(f"/recipes/ingredients/{ingredient_id}")
        if resp.status_code == 200:
            return resp.json()
        logger.warning(
            "recipe-service returned %s for ingredient %s",
            resp.status_code,
            ingredient_id,
        )
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch ingredient %s: %s", ingredient_id, exc)
    return None


async def fetch_ingredients_bulk(ingredient_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch multiple ingredients in parallel.
    Returns a dict mapping ingredient_id → ingredient data.
    """
    import asyncio

    results: Dict[str, Dict[str, Any]] = {}

    async def _fetch_one(iid: str):
        data = await fetch_ingredient(iid)
        if data:
            results[iid] = data

    await asyncio.gather(*[_fetch_one(iid) for iid in set(ingredient_ids)])
    return results


def convert_to_grams(quantity: float, unit: str) -> float:
    """
    Convert a quantity in any CapacityUnit to grams using the lookup table.
    Falls back to treating the value as grams when the unit is unknown.
    """
    factor = UNIT_TO_GRAMS.get(unit, 1.0)
    return round(quantity * factor, 2)
