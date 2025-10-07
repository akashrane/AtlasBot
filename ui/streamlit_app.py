# ui/streamlit_app.py
import sys, os, re, html
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from tools.atlas_logic import play_turn, reset_game  # backend logic & reset

# -------------------------------
# Page & Session Configuration
# -------------------------------
st.set_page_config(page_title="🌍 Atlas AI Game", page_icon="🌎", layout="wide")

# Initialize session state
if "chat" not in st.session_state:
    st.session_state.chat = []  # list of dicts: {"user","bot","place","map_ok","coords":(lat,lon)}
if "score" not in st.session_state:
    st.session_state.score = 0
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "All Geography"
if "next_letter" not in st.session_state:
    st.session_state.next_letter = None
if "show_map" not in st.session_state:
    st.session_state.show_map = True
if "zoom" not in st.session_state:
    st.session_state.zoom = 4

# -------------------------------
# Helpers
# -------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def geocode_place(place: str):
    """Geocode a place name via Nominatim (cached). Returns (lat, lon) or None."""
    try:
        params = {"q": place, "format": "json", "limit": 1}
        headers = {"User-Agent": "AtlasBot/1.0", "Accept-Language": "en"}
        r = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers, timeout=10)
        if r.ok and r.json():
            j = r.json()[0]
            return float(j["lat"]), float(j["lon"])
    except Exception:
        pass
    return None

PLACE_REGEX = re.compile(r"My turn\s*\((?P<type>[^)]+)\)\s*:\s*(?P<place>.+?)(?:\.|\n|$)", re.IGNORECASE)
LETTER_REGEX = re.compile(r"next place should start with\s*'(?P<letter>[A-Za-z])'", re.IGNORECASE)

def parse_bot_message(msg: str):
    """Extract (place, next_letter) from bot text robustly."""
    place = None
    next_letter = None
    m = PLACE_REGEX.search(msg)
    if m:
        place = m.group("place").strip()
    m2 = LETTER_REGEX.search(msg)
    if m2:
        next_letter = m2.group("letter").upper()
    # fallback: if we couldn't parse, try after first colon up to 'Your'
    if not place and ":" in msg:
        place = msg.split(":", 1)[1].split("Your")[0].strip()
    return place, next_letter

def reset_ui_and_backend():
    reset_game()
    st.session_state.chat = []
    st.session_state.score = 0
    st.session_state.next_letter = None

# -------------------------------
# Sidebar Controls
# -------------------------------
st.sidebar.header("🎮 Game Settings")
st.session_state.difficulty = st.sidebar.radio(
    "Select Difficulty Level:",
    ["Countries Only", "Cities + States", "All Geography"],
    index=["Countries Only", "Cities + States", "All Geography"].index(st.session_state.difficulty),
    help="Controls what the bot is allowed to play."
)

st.sidebar.checkbox("Show map for each bot move", value=st.session_state.show_map, key="show_map")
st.sidebar.slider("Map zoom", 2, 10, value=st.session_state.zoom, step=1, key="zoom")

with st.sidebar.expander("Used places (this session)"):
    if st.session_state.chat:
        st.write(", ".join(sorted({c["place"] for c in st.session_state.chat if c.get("place")})))
    else:
        st.caption("No places yet.")

if st.sidebar.button("🔁 Restart Game", help="Clears the chat, score, and backend memory."):
    reset_ui_and_backend()
    st.sidebar.success("✅ Game restarted.")

# -------------------------------
# Header
# -------------------------------
st.title("🌍 Atlas AI — Play Geography with an Agentic Bot")
st.caption("Built with OpenStreetMap, RestCountries API, and OpenAI Agent logic 💬")

# Status row: Next letter + Difficulty
status_cols = st.columns([1, 1])
with status_cols[0]:
    chip = st.session_state.next_letter or "—"
    st.markdown(f"**Next letter:** :blue[{chip}]")
with status_cols[1]:
    st.markdown(f"**Mode:** :violet[{st.session_state.difficulty}]")

st.write("---")

# -------------------------------
# Input Form (debounced submit)
# -------------------------------
with st.form("atlas_input_form", clear_on_submit=True):
    user_input = st.text_input(
        "Enter your place:",
        placeholder="e.g., India, Paris, or Asia",
        help="Type a valid place that starts with the required letter."
    )
    submitted = st.form_submit_button("Submit", use_container_width=True)

if submitted and user_input:
    with st.spinner("Thinking…"):
        try:
            result = play_turn(user_input, difficulty=st.session_state.difficulty)
        except Exception as e:
            st.error("The game logic encountered an error. Please try again.")
            st.stop()

        # Store message safely (escape user/bot content to avoid HTML injection)
        bot_text = result.get("response", "")
        safe_user = html.escape(user_input)
        safe_bot = html.escape(bot_text)

        # Parse the bot message to extract the place and next letter
        place_name, next_letter = parse_bot_message(bot_text)
        st.session_state.next_letter = next_letter or st.session_state.next_letter

        # Attempt geocode of the bot's place (cached)
        coords = geocode_place(place_name) if place_name else None
        map_ok = coords is not None

        # Append to chat history
        st.session_state.chat.append(
            {
                "user": safe_user,
                "bot": safe_bot,
                "place": place_name,
                "map_ok": map_ok,
                "coords": coords,
                "raw": bot_text,
            }
        )

        # Score only on valid turns
        if "Invalid move" not in bot_text and "You win" not in bot_text:
            st.session_state.score += 1

st.caption("💡 Press **Enter** or click **Submit** to send your move.")

# -------------------------------
# Chat Display (newest first)
# -------------------------------
for entry in reversed(st.session_state.chat):
    # User message
    st.markdown(
        f"""
        <div style='padding:12px;background-color:#1e1f24;border-radius:10px;margin-bottom:10px;'>
            <div style='color:#ffd43b;font-weight:600'>🧭 You:</div>
            <div style='font-size:18px;color:#ffffff;margin-top:4px;'><b>{entry['user']}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Highlight the bot's place inside the bot text (safe, controlled)
    bot_text = entry["raw"]  # original
    place_name = entry.get("place") or ""
    if place_name:
        highlighted = html.escape(bot_text).replace(
            html.escape(place_name),
            f"<span style='color:#00f7ff;font-weight:700'>{html.escape(place_name)}</span>"
        )
    else:
        highlighted = html.escape(bot_text)

    st.markdown(
        f"""
        <div style='background-color:#262730;border-left:5px solid #00c3ff;
                    padding:15px;border-radius:10px;margin-bottom:10px;'>
            <div style='color:#00c3ff;font-weight:600'>🤖 AtlasBot:</div>
            <div style='font-size:17px;color:#e6e6e6;margin-top:4px;'>{highlighted}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Map for the bot's suggested place (toggle + cached geocode)
    if st.session_state.show_map and entry.get("place") and entry.get("map_ok"):
        lat, lon = entry["coords"]
        try:
            m = folium.Map(location=[lat, lon], zoom_start=st.session_state.zoom)
            folium.Marker(
                [lat, lon],
                popup=entry["place"],
                tooltip=f"📍 {entry['place']}",
                icon=folium.Icon(color="blue", icon="globe")
            ).add_to(m)
            st.markdown("🌐 **Bot's Suggested Location:**")
            st_folium(m, width=770, height=420)
        except Exception:
            st.info("ℹ️ Map could not be rendered for this location on your device.")

st.write("---")

# -------------------------------
# Scoreboard / Footer
# -------------------------------
cols = st.columns(3)
with cols[0]:
    st.metric("🏆 Your Score", st.session_state.score)
with cols[1]:
    st.metric("🌐 Difficulty", st.session_state.difficulty)
with cols[2]:
    st.metric("🧭 Next letter", st.session_state.next_letter or "—")

st.caption("🧠 Follow Atlas rules: reply with a valid place that starts with the required letter. Type `quit`, `reset`, or use the sidebar to restart.")
st.caption("Developed by Akash Rane • Maps © OpenStreetMap contributors")
