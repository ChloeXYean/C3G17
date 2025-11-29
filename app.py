import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime, timezone

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="KLCC Live PM2.5", layout="centered")
st.title("KLCC Kuala Lumpur")
st.markdown("### Real-time PM2.5 Air Quality")

# KLCC coordinates (fallback)
KLCC_LAT = 3.1579
KLCC_LON = 101.7123

# OpenAQ endpoint
API_URL = "https://api.openaq.org/v3/locations/5893160/latest"


# ==================== API FETCH FUNCTION ====================
def get_latest_pm25():
    try:
        API_KEY = "dc213ab59e72d5a2ad42b90957e9e531117bf633a774b6157751bae99dce8af6" 

        response = requests.get(
            API_URL,
            headers={"X-API-Key": API_KEY}  
        )
        response.raise_for_status()

        data = response.json()
        record = data["results"][0]

        return {
            "pm25": record["value"],
            "lat": record["coordinates"]["latitude"],
            "lon": record["coordinates"]["longitude"],
            "updated": record["datetime"]["local"],
            "location": "KLCC"
        }

    except Exception as e:
        st.error(f"Error fetching API: {e}")
        return None


# ==================== REFRESH BUTTON ====================
if st.button("🔄 Refresh Data", type="primary"):
    st.cache_data.clear()
    st.rerun()


# ==================== FETCH DATA ====================
with st.spinner("Fetching KLCC PM2.5..."):
    result = get_latest_pm25()

# If API fails
if result is None:
    st.error("❌ No PM2.5 data available. API returned no results.")
    st.stop()

# Extract data
pm25 = result["pm25"]
lat = result["lat"]
lon = result["lon"]
updated_display = result["updated"]
location = result["location"]

# ==================== AQI COLOR ====================
if pm25 <= 12:
    color, status = "green", "Good"
elif pm25 <= 35:
    color, status = "yellow", "Moderate"
elif pm25 <= 55:
    color, status = "orange", "Unhealthy for Sensitive Groups"
elif pm25 <= 150:
    color, status = "red", "Unhealthy"
else:
    color, status = "purple", "Very Unhealthy"

# ==================== SIDEBAR INDICATOR ====================
st.sidebar.success("🟢 Using REAL LIVE DATA from OpenAQ.")
st.sidebar.info("Data: OpenAQ v3 API (Clarity Node-S)\nUpdated every 10–30 minutes.")

# ==================== DISPLAY INFO ====================
col1, col2 = st.columns([1, 2])

with col1:
    st.metric("PM2.5", f"{pm25} µg/m³")
    st.markdown(f"**{status}**")
    st.caption(f"Location: {location}\nUpdated: {updated_display}")

with col2:
    m = folium.Map(location=[lat, lon], zoom_start=16, tiles="CartoDB positron")
    folium.CircleMarker(
        [lat, lon],
        radius=15,
        popup=f"{location}<br>PM2.5: {pm25} µg/m³<br>Updated: {updated_display}",
        tooltip=f"{pm25} µg/m³",
        color="black",
        weight=3,
        fillColor=color,
        fillOpacity=0.9
    ).add_to(m)
    st_folium(m, width=700, height=400)

st.success("✓ Page loaded successfully.")
