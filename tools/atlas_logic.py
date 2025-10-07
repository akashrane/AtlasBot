import random
import requests
import time

# --- Game State ---
used_places = set()
last_required_letter = None

# --- Load countries once ---
def get_country_list():
    try:
        resp = requests.get("https://restcountries.com/v3.1/all", timeout=10)
        data = resp.json()
        return sorted([c["name"]["common"] for c in data])
    except Exception:
        return ["India", "Argentina", "Brazil", "Canada", "France", "Japan", "Kenya", "Mexico"]

COUNTRIES = get_country_list()

# --- Helpers ---
def reset_game():
    """Resets the global game state."""
    global used_places, last_required_letter
    used_places.clear()
    last_required_letter = None
    return "✅ Game has been reset!"

def detect_type(place_name):
    """Detect if input is country/city/state/continent."""
    place = place_name.strip().capitalize()
    if place in COUNTRIES:
        return "country"

    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place, "format": "json", "addressdetails": 1, "limit": 1}
        headers = {"User-Agent": "AtlasBot/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if not resp.ok or not resp.json():
            return "unknown"
        address = resp.json()[0].get("address", {})
        if "city" in address:
            return "city"
        elif "state" in address:
            return "state"
        elif "country" in address:
            return "country"
        elif "continent" in address:
            return "continent"
        return "unknown"
    except Exception:
        return "unknown"


def find_place_by_letter(letter, place_type="country", difficulty="All Geography"):
    """Find a valid next place depending on the selected difficulty."""
    time.sleep(1)
    letter = letter.lower()

    # --- Countries Only mode ---
    if difficulty == "Countries Only":
        possible = [c for c in COUNTRIES if c.lower().startswith(letter)]
        available = [c for c in possible if c.lower() not in used_places]
        # Try fallback if all are used
        if not available and possible:
            available = possible
        return random.choice(available) if available else None

    # --- Cities + States mode ---
    if difficulty == "Cities + States":
        return find_geo_place(letter, ["city", "state"])

    # --- All Geography mode ---
    return find_geo_place(letter, ["city", "state", "country", "continent"])


def find_geo_place(letter, allowed_types):
    """Helper function to query Nominatim for cities/states/countries."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": letter, "format": "json", "addressdetails": 1, "limit": 100}
    headers = {"User-Agent": "AtlasBot/1.0"}
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    if not resp.ok:
        return None
    data = resp.json()

    candidates = []
    for item in data:
        addr = item.get("address", {})
        if any(k in addr for k in allowed_types):
            name = item.get("display_name", "").split(",")[0]
            if len(name) > 3 and name.lower().startswith(letter):
                candidates.append(name)
    candidates = list(set(candidates))  # unique only
    return random.choice(candidates) if candidates else None


def play_turn(user_place, difficulty="All Geography"):
    """Core Atlas game logic."""
    global last_required_letter, used_places

    user_place = user_place.strip().capitalize()

    # Handle reset
    if user_place.lower() in ["quit", "restart"]:
        return {"response": reset_game(), "map": None}

    # Validate turn
    if last_required_letter and not user_place.lower().startswith(last_required_letter):
        return {"response": f"❌ Invalid move! You must enter a place starting with '{last_required_letter.upper()}'.", "map": None}

    used_places.add(user_place.lower())
    place_type = detect_type(user_place)
    last_letter = user_place[-1].lower()

    # Find bot's next move
    bot_place = find_place_by_letter(last_letter, place_type, difficulty)

    if not bot_place:
        return {"response": f"I couldn't find any {place_type} starting with '{last_letter.upper()}'. You win!", "map": None}

    # Update last letter only after a valid move
    used_places.add(bot_place.lower())
    last_required_letter = bot_place[-1].lower()

    return {
        "response": f"My turn ({place_type}): {bot_place}. Your next place should start with '{last_required_letter.upper()}'.",
        "map": f"https://nominatim.openstreetmap.org/ui/search.html?q={bot_place}"
    }
