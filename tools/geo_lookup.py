# tools/geo_lookup.py
from __future__ import annotations
import time
import requests
from functools import lru_cache

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOM_HEADERS = {"User-Agent": "AtlasAI/1.0 (educational project)", "Accept-Language": "en"}
NOM_LIMIT = 1
NOM_COOLDOWN = 0.6  # be polite to the service

@lru_cache(maxsize=512)
def lookup_coords(place: str) -> dict | None:
    """
    Return {'lat': float, 'lon': float, 'display': str} for a place,
    or None if not found.
    """
    q = (place or "").strip()
    if not q:
        return None

    # small cooldown to avoid hammering the endpoint
    time.sleep(NOM_COOLDOWN)
    try:
        r = requests.get(
            NOMINATIM_URL,
            params={"q": q, "format": "json", "addressdetails": 1, "limit": NOM_LIMIT},
            headers=NOM_HEADERS,
            timeout=10,
        )
        if not r.ok:
            return None
        items = r.json() or []
        if not items:
            return None
        it = items[0]
        lat = float(it.get("lat"))
        lon = float(it.get("lon"))
        disp = it.get("display_name", q).split(",")[0]
        return {"lat": lat, "lon": lon, "display": disp}
    except Exception:
        return None
