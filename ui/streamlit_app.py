import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from tools.atlas_logic import play_turn

# ------------------------------------------------------
# Page & Session Config
# ------------------------------------------------------
st.set_page_config(page_title="🌍 Atlas AI Game", page_icon="🌎", layout="wide")

if "chat" not in st.session_state:
    st.session_state.chat = []
if "score" not in st.session_state:
    st.session_state.score = 0
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "All Geography"

# ------------------------------------------------------
# Sidebar Controls
# ------------------------------------------------------
st.sidebar.header("🎮 Game Settings")
difficulty = st.sidebar.radio(
    "Select Difficulty Level:",
    ["Countries Only", "Cities + States", "All Geography"],
    index=["Countries Only", "Cities + States", "All Geography"].index(st.session_state.difficulty),
)
st.session_state.difficulty = difficulty

if st.sidebar.button("🔁 Restart Game"):
    from tools.atlas_logic import reset_game
    reset_game()
    st.session_state.chat = []
    st.session_state.score = 0
    st.sidebar.success("✅ Game restarted successfully!")


# ------------------------------------------------------
# Header
# ------------------------------------------------------
st.title("🌍 Atlas AI — Play Geography with an Agentic Bot")
st.caption("Built with OpenStreetMap, RestCountries API, and OpenAI Agent logic 💬")

# ------------------------------------------------------
# Input Form
# ------------------------------------------------------
with st.form("atlas_input_form", clear_on_submit=True):
    user_input = st.text_input("Enter your place:", placeholder="e.g., India, Paris, or Asia")
    submitted = st.form_submit_button("Submit")

if submitted and user_input:
    result = play_turn(user_input, difficulty=st.session_state.difficulty)
    st.session_state.chat.append(
        {
            "user": user_input,
            "bot": result["response"],
            "map": result["map"],
        }
    )
    if "Invalid move" not in result["response"]:
        st.session_state.score += 1

st.caption("💡 Press **Enter** or click **Submit** to send your move.")

# ------------------------------------------------------
# Chat Display
# ------------------------------------------------------
for entry in reversed(st.session_state.chat):
    # User message
    st.markdown(
        f"""
        <div style='padding:10px;background-color:#202020;border-radius:8px;margin-bottom:10px;'>
            <h4 style='color:#ffd43b;'>🧭 You:</h4>
            <p style='font-size:18px;color:#fff;margin-top:-10px;'><b>{entry['user']}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Extract just the place name from bot text (after first colon)
    bot_text = entry["bot"]
    if ":" in bot_text:
        place_name = bot_text.split(":", 1)[1].split("Your")[0].strip()
    else:
        place_name = bot_text.strip()

    # Bot message with highlighted place
    st.markdown(
        f"""
        <div style='background-color:#262730;border-left:5px solid #00c3ff;
                    padding:15px;border-radius:8px;margin-bottom:10px;'>
            <h4 style='color:#00c3ff;'>🤖 AtlasBot:</h4>
            <p style='font-size:17px;color:#e6e6e6;margin-bottom:8px;'>
                {bot_text.replace(place_name, f"<span style='color:#00f7ff;font-weight:bold;'>{place_name}</span>")}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # Map showing BOT's suggested place only
    # --------------------------------------------------
    if entry["map"]:
        try:
            query = place_name
            params = {"q": query, "format": "json", "limit": 1}
            headers = {"User-Agent": "AtlasBot/1.0"}
            resp = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers)

            if resp.ok and resp.json():
                data = resp.json()[0]
                lat, lon = float(data["lat"]), float(data["lon"])
                m = folium.Map(location=[lat, lon], zoom_start=4)
                folium.Marker(
                    [lat, lon],
                    popup=query,
                    tooltip=f"📍 {query}",
                    icon=folium.Icon(color="blue", icon="globe")
                ).add_to(m)
                st.markdown("🌐 **Bot's Suggested Location:**")
                st_folium(m, width=700, height=400)
            else:
                st.info("ℹ️ Map not found for this location.")
        except Exception:
            st.warning("⚠️ Could not display map for this location.")

st.divider()

# ------------------------------------------------------
# Scoreboard / Footer
# ------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    st.metric("🏆 Your Score", st.session_state.score)
with col2:
    st.metric("🌐 Difficulty", st.session_state.difficulty)

st.caption("🧠 Type a valid place following Atlas rules. Type `quit` to stop.")
st.caption("Developed by Akash Rane")