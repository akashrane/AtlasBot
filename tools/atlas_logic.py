import csv
import os
import random
import time
import unicodedata
from typing import Dict, List, Optional, Tuple

import requests

# =========================
# Global Game State
# =========================
used_places: set[str] = set()
last_required_letter: Optional[str] = None

# =========================
# Config
# =========================
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
COUNTRIES_CSV = os.path.join(DATA_DIR, "countries.csv")

# Nominatim (for city/state lookups in non-country modes)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOM_HEADERS = {"User-Agent": "AtlasAI/1.0 (educational project)", "Accept-Language": "en"}
NOM_LIMIT = 150
NOM_COOLDOWN = 0.8  # be nice to the service

# Continents (fixed)
CONTINENTS = [
    "Africa", "Antarctica", "Asia", "Europe",
    "North America", "Oceania", "South America",
]

# In-memory caches
_COUNTRIES: List[Dict[str, str]] = []               # [{display, canon}]
_COUNTRIES_BY_LETTER: Dict[str, List[Dict[str, str]]] = {}
_CITY_CACHE: Dict[str, List[Tuple[str, float]]] = {}  # letter -> [(name, importance)]
_STATE_CACHE: Dict[str, List[Tuple[str, float]]] = {} # letter -> [(name, importance)]

# Aliases (canonicalization)
ALIASES = {
    "usa": "United States",
    "u.s.a": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k": "United Kingdom",
    "burma": "Myanmar",
    "swaziland": "Eswatini",
    "ivory coast": "Côte d'Ivoire",
    "east timor": "Timor-Leste",
    "macedonia": "North Macedonia",
    "czech republic": "Czechia",
    "south korea": "South Korea",
    "north korea": "North Korea",
    "turkey": "Türkiye",
    "cape verde": "Cabo Verde",
    "congo-brazzaville": "Congo",
    "drc": "Democratic Republic of the Congo",
    "dr congo": "Democratic Republic of the Congo",
}

# =========================
# Helpers
# =========================
def _strip_diacritics(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def canon(s: str) -> str:
    s = _strip_diacritics(s).strip().lower()
    s = " ".join(s.split())
    return ALIASES.get(s, s)

def last_alpha(name: str) -> Optional[str]:
    for ch in reversed(_strip_diacritics(name).lower()):
        if ch.isalpha():
            return ch
    return None

def _ensure_data_dir():
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# Countries: load + index
# =========================
def load_countries() -> None:
    """Load canonical countries from CSV and build per-letter index."""
    global _COUNTRIES, _COUNTRIES_BY_LETTER
    if _COUNTRIES:
        return
    _ensure_data_dir()
    if not os.path.exists(COUNTRIES_CSV):
        raise RuntimeError(f"countries.csv not found at {COUNTRIES_CSV}")

    rows: List[str] = []
    with open(COUNTRIES_CSV, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            # allow plain lines or CSV with one column
            name = row[0].strip()
            if name and not name.startswith("#"):
                rows.append(name)

    # Build canonical dicts
    _COUNTRIES = [{"display": n, "canon": canon(n)} for n in rows]

    # Deduplicate by canon, keep first display
    seen: Dict[str, Dict[str, str]] = {}
    for it in _COUNTRIES:
        seen.setdefault(it["canon"], it)
    _COUNTRIES = list(seen.values())

    # Index per letter
    _COUNTRIES_BY_LETTER = {chr(c): [] for c in range(ord("a"), ord("z") + 1)}
    for it in _COUNTRIES:
        cfirst = it["canon"][0]
        if "a" <= cfirst <= "z":
            _COUNTRIES_BY_LETTER[cfirst].append(it)

# =========================
# Difficulty & detection
# =========================
def detect_type(place_name: str) -> str:
    """Very strict: country if in countries list, continent if in fixed list, else city/state/unknown via Nominatim."""
    load_countries()
    p = place_name.strip()
    if not p:
        return "unknown"

    pc = canon(p)
    if any(pc == it["canon"] for it in _COUNTRIES):
        return "country"
    if pc in (canon(c) for c in CONTINENTS):
        return "continent"

    # Ask Nominatim only to distinguish city/state
    try:
        r = requests.get(
            NOMINATIM_URL,
            params={"q": p, "format": "json", "addressdetails": 1, "limit": 1},
            headers=NOM_HEADERS,
            timeout=10,
        )
        j = r.json() if r.ok else []
        if j:
            addr = j[0].get("address", {})
            typ = j[0].get("type", "")
            if "city" in addr or typ in {"city", "town"}:
                return "city"
            if any(k in addr for k in ("state", "region", "province")):
                return "state"
    except Exception:
        pass
    return "unknown"

# =========================
# Selection tiers (never concede early)
# =========================
def pick_country(letter: str) -> Optional[str]:
    """Deterministic, fallback-safe country selection."""
    load_countries()
    L = letter.lower()
    pool = _COUNTRIES_BY_LETTER.get(L, [])

    def unused(arr): return [it for it in arr if it["canon"] not in used_places]

    # Tier 1: Unused countries starting with L
    t1 = unused(pool)
    if t1:
        return random.choice(t1)["display"]

    # Tier 2: Allow repeats within that letter
    if pool:
        return random.choice(pool)["display"]

    # Tier 3: emergency global scan by letter
    gpool = [it for it in _COUNTRIES if it["canon"].startswith(L)]
    t3 = unused(gpool)
    if t3:
        return random.choice(t3)["display"]
    return random.choice(gpool)["display"] if gpool else None

# Simple continent picker (rarely used)
def pick_continent(letter: str) -> Optional[str]:
    L = letter.lower()
    opts = [c for c in CONTINENTS if canon(c).startswith(L)]
    if not opts:
        return None
    u = [c for c in opts if canon(c) not in used_places]
    return random.choice(u or opts)

# =========================
# Cities & States via Nominatim (cached)
# =========================
def _nominatim_letter_index(letter: str, kind: str) -> List[Tuple[str, float]]:
    """Fetch and cache city/state candidates for a starting letter."""
    cache = _CITY_CACHE if kind == "city" else _STATE_CACHE
    if letter in cache:
        return cache[letter]

    time.sleep(NOM_COOLDOWN)
    params = {"q": letter, "format": "json", "addressdetails": 1, "limit": NOM_LIMIT, "extratags": 1}
    out: List[Tuple[str, float]] = []
    try:
        r = requests.get(NOMINATIM_URL, params=params, headers=NOM_HEADERS, timeout=12)
        items = r.json() if r.ok else []
        for it in items:
            name = it.get("display_name", "").split(",")[0]
            if not name or not name.isascii():
                continue
            if canon(name)[:1] != letter:
                continue
            iclass, itype = it.get("class"), it.get("type")
            if kind == "city" and iclass == "place" and itype in {"city", "town"}:
                out.append((name, float(it.get("importance", 0.0))))
            if kind == "state":
                addr = it.get("address", {})
                if any(k in addr for k in ("state", "region", "province")) and iclass in {"place", "boundary"}:
                    out.append((name, float(it.get("importance", 0.0))))
    except Exception:
        pass

    # Sort by importance, keep top 40 for quality/variety
    out.sort(key=lambda x: x[1], reverse=True)
    cache[letter] = out[:40]
    return cache[letter]

def pick_city(letter: str) -> Optional[str]:
    cands = _nominatim_letter_index(letter, "city")
    unused = [n for n, _ in cands if canon(n) not in used_places]
    return random.choice(unused or [n for n, _ in cands]) if cands else None

def pick_state(letter: str) -> Optional[str]:
    cands = _nominatim_letter_index(letter, "state")
    unused = [n for n, _ in cands if canon(n) not in used_places]
    return random.choice(unused or [n for n, _ in cands]) if cands else None

# =========================
# Public API
# =========================
def reset_game() -> str:
    global used_places, last_required_letter
    used_places.clear()
    last_required_letter = None
    return "🔁 Game reset! Let's start fresh."

def find_place_by_letter(letter: str, user_type: str, difficulty: str) -> Optional[str]:
    """Central router with strict difficulty gates and fallbacks."""
    L = letter.lower()

    if difficulty == "Countries Only":
        return pick_country(L)

    if user_type == "country":
        return pick_country(L)
    if user_type == "continent":
        return pick_continent(L)

    # Cities + States mode
    if difficulty == "Cities + States":
        first = pick_city(L)
        if first:
            return first
        return pick_state(L)

    # All Geography: prefer same type, then broaden
    if user_type == "city":
        return pick_city(L) or pick_state(L) or pick_country(L) or pick_continent(L)
    if user_type == "state":
        return pick_state(L) or pick_city(L) or pick_country(L) or pick_continent(L)

    # unknown → broadest
    return pick_city(L) or pick_state(L) or pick_country(L) or pick_continent(L)

def play_turn(user_place: str, difficulty: str = "All Geography"):
    """Main game API used by Streamlit."""
    global last_required_letter

    name = user_place.strip()
    if not name:
        return {"response": "💬 Please enter a place.", "map": None}

    cn = canon(name)
    if cn in {"quit", "restart", "reset"}:
        return {"response": reset_game(), "map": None}

    # Rule: enforce starting letter after first move
    if last_required_letter and cn[:1] != last_required_letter:
        return {"response": f"❌ Invalid move! Your place must start with **{last_required_letter.upper()}**.", "map": None}

    # Detect type
    ptype = detect_type(name)

    # Mode gate
    if difficulty == "Countries Only" and ptype != "country":
        return {"response": "🌍 Countries Only mode — please enter a **country** (e.g., India, France, Japan).", "map": None}
    if difficulty == "Cities + States" and ptype not in {"city", "state"}:
        return {"response": "🏙️ Cities + States mode — please enter a **city or state**.", "map": None}

    # Record user's place
    used_places.add(cn)

    # Find bot response
    last = last_alpha(name)
    if not last:
        return {"response": "⚠️ I couldn’t find a valid ending letter in that name. Try another place.", "map": None}

    bot = find_place_by_letter(last, ptype, difficulty)
    if not bot:
        # With our tiers this should basically never happen for countries;
        # still keep a graceful message.
        return {"response": f"🏁 I truly couldn’t find anything starting with **{last.upper()}**. You win! 🎉", "map": None}

    used_places.add(canon(bot))
    last_required_letter = last_alpha(bot) or None

    return {
        "response": f"🤖 My turn ({'country' if difficulty=='Countries Only' else ptype}): {bot}. Your next place should start with **{(last_required_letter or '—').upper()}**.",
        "map": f"https://nominatim.openstreetmap.org/ui/search.html?q={bot.replace(' ', '+')}"
    }
