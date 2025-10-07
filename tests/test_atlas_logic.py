# tests/test_atlas_logic.py
import string
from tools.atlas_logic import load_countries, _COUNTRIES_BY_LETTER, pick_country

def test_every_letter_has_country():
    load_countries()
    missing = [L for L in string.ascii_lowercase if not _COUNTRIES_BY_LETTER.get(L)]
    # a few letters may legitimately be empty in CSV (e.g., 'x')
    assert set(missing).issubset({"x"}), f"Missing letters in countries index: {missing}"

def test_pick_country_never_none():
    load_countries()
    for L in "abcdefghijklmnopqrstuvwxyz":
        if L == "x":
            continue
        assert pick_country(L) is not None
