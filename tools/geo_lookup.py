# tools/geo_lookup.py
import requests

def geo_lookup(place_name: str):
    """
    Uses OpenStreetMap's Nominatim API to get details about a place.
    Works for cities, states, countries, and continents.
    """
    url = f"https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }
    headers = {"User-Agent": "AtlasBot/1.0"}
    resp = requests.get(url, params=params, headers=headers)
    
    if resp.status_code != 200 or not resp.json():
        return {"error": "Place not found"}

    data = resp.json()[0]
    address = data.get("address", {})

    # Determine type of place
    place_type = None
    if "country" in address:
        place_type = "country"
    elif "state" in address:
        place_type = "state"
    elif "city" in address:
        place_type = "city"
    elif "continent" in address:
        place_type = "continent"
    else:
        place_type = "unknown"

    result = {
        "name": data.get("display_name"),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "type": place_type
    }
    return result
