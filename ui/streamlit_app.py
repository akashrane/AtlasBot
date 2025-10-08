# ui/streamlit_app.py

# --- PYTHONPATH bootstrap so we can import sibling package "tools" when running from ui/ ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  # repo root (parent of ui/)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ------------------------------------------------------------------------------------------

import re
from typing import Dict, Any, Optional

import streamlit as st

# Optional folium rendering (clean map); we gracefully fall back to st.map if missing
try:
    from streamlit_folium import st_folium
    import folium
    HAS_FOLIUM = True
except Exception:
    HAS_FOLIUM = False

# Engine: single source of truth
from tools.atlas_logic import play_turn, reset_game, get_state
from tools.geo_lookup import lookup_coords

# ---------- Page config ----------
st.set_page_config(
    page_title="Atlas AI — Play Geography with an Agentic Bot",
    page_icon="🌍",
    layout="wide",
)

# ---------- Helpers ----------
def message_card(text: str, role: str = "user") -> None:
    """Render a simple, readable card for user/bot messages."""
    if role == "user":
        bg = "#171717"; border = "#2d2d2d"; title = "🧭 **You:**"
    else:
        bg = "#1f2430"; border = "#2a2f3a"; title = "🤖 **AtlasBot:**"
    st.markdown(
        f"""
        <div style="
            background:{bg};
            border:1px solid {border};
            border-radius:12px;
            padding:14px 16px;
            margin:6px 0 8px 0;
        ">
          <div style="opacity:.9;margin-bottom:6px">{title}</div>
          <div style="font-size:0.98rem;line-height:1.5">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def extract_bot_place(bot_text: str) -> Optional[str]:
    """
    Bot replies look like: "🤖 My turn (country): Argentina. Your next place should start with 'A'."
    Extract 'Argentina' robustly.
    """
    if not bot_text:
        return None
    # try "): <place>. Your next"
    m = re.search(r"\):\s*(.+?)\.\s+Your next", bot_text)
    if m:
        return m.group(1).strip()
    # fallback: after "): "
    m = re.search(r"\):\s*(.+)$", bot_text)
    if m:
        return m.group(1).strip()
    return None

def render_clean_map_for_place(name: str, zoom: int) -> None:
    """Draw a clean map (no UI) centered on the bot's place name."""
    geo = lookup_coords(name)
    if not geo:
        return
    lat, lon, disp = geo["lat"], geo["lon"], geo["display"]

    st.markdown("**🗺️ Bot's Suggested Location:**")
    if HAS_FOLIUM:
        m = folium.Map(location=[lat, lon], zoom_start=zoom, control_scale=True, tiles="OpenStreetMap")
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color="#3B82F6",
            fill=True,
            fill_opacity=0.8,
            popup=disp,
        ).add_to(m)
        st_folium(m, height=int(220 + zoom * 12), width=None)
    else:
        # Fallback: light-weight map (no extra deps)
        import pandas as pd
        st.info("For a nicer map, install: pip install folium streamlit-folium")
        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

def soft_divider():
    st.markdown('<hr style="border:none;border-top:1px solid #2a2a2a;margin:12px 0 6px 0" />', unsafe_allow_html=True)

# ---------- Sidebar (controls) ----------
with st.sidebar:
    st.header("🎮 Game Settings")

    difficulty = st.radio(
        "Select Difficulty Level:",
        options=["Countries Only", "Cities + States", "All Geography"],
        index=["Countries Only", "Cities + States", "All Geography"].index(
            st.session_state.get("difficulty", "All Geography")
        ),
        key="difficulty",
    )

    show_map = st.checkbox(
        "Show map for each bot move",
        value=st.session_state.get("show_map", True),
        key="show_map",
    )
    map_zoom = st.slider("Map zoom", min_value=4, max_value=12, value=st.session_state.get("map_zoom", 8), key="map_zoom")

    soft_divider()

    # Authoritative state from the engine
    state = get_state()
    with st.expander("🧾 Used places (this session)", expanded=True):
        if state["used_places"]:
            st.write(", ".join(state["used_places"]))
        else:
            st.caption("No places yet.")

    soft_divider()

    if st.button("🔁 Restart Game"):
        reset_game()
        st.session_state["messages"] = []
        st.success("Game reset!")
        st.experimental_rerun()

# ---------- Header ----------
st.title("Atlas AI — Play Geography with an Agentic Bot")

# Show next letter + mode from engine state
state = get_state()
col1, col2, col3 = st.columns([1, 1.2, 6])
with col1:
    st.caption("Next letter:")
    st.subheader((state["last_required_letter"] or "—").upper())
with col2:
    st.caption("Mode:")
    st.subheader(difficulty)

soft_divider()

# ---------- Chat state ----------
if "messages" not in st.session_state:
    st.session_state["messages"] = []  # list of dicts: {"role": "user"|"bot", "text": str}

# ---------- Input form ----------
with st.form("atlas_input", clear_on_submit=True):
    place = st.text_input("Enter your place:", placeholder="e.g., India, Paris, or Asia")
    submitted = st.form_submit_button("Submit")

if submitted:
    user_place = place.strip()
    if not user_place:
        st.warning("Please enter a place.")
    else:
        st.session_state["messages"].append({"role": "user", "text": user_place})

        # Ask engine to play
        result = play_turn(user_place, difficulty=difficulty)
        st.session_state["messages"].append({"role": "bot", "text": result["response"]})

# ---------- Conversation (NEWEST FIRST) ----------
for msg in reversed(st.session_state["messages"]):
    if msg["role"] == "user":
        message_card(msg["text"], role="user")
    else:
        message_card(msg["text"], role="bot")
        if show_map:
            bot_place = extract_bot_place(msg["text"])
            if bot_place:
                render_clean_map_for_place(bot_place, zoom=map_zoom)

soft_divider()

# ---------- Footer ----------
c1, c2, c3 = st.columns([2, 3, 5])
with c1:
    st.caption("🏆 Your Score")
    user_moves = sum(1 for m in st.session_state["messages"] if m["role"] == "user")
    st.subheader(str(user_moves))
with c2:
    st.caption("🌐 Difficulty")
    st.subheader(difficulty)
with c3:
    st.caption("🧭 Next letter")
    st.subheader((get_state()["last_required_letter"] or "—").upper())

st.caption("Developed by Akash Rane • Maps © OpenStreetMap contributors")
