# combine_fixed.py
import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
import os

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="KLCC Live PM2.5", layout="centered")
st.title("KLCC Kuala Lumpur")
st.markdown("### Real-time PM2.5 Air Quality")

KLCC_LAT = 3.1579
KLCC_LON = 101.7123
API_URL = "https://api.openaq.org/v3/locations/5893160/latest"
HISTORY_FILE = "pm25_history.csv"

# ==================== ROBUST HISTORY FUNCTIONS ====================
def save_reading(pm25, time_str):
    line = f"{time_str},{pm25}\n"
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("Time,PM2.5\n")
    
    # Prevent duplicates
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                if time_str in f.read():
                    return False
        except:
            pass
    
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    return True

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["Time", "PM2.5"])
    try:
        df = pd.read_csv(HISTORY_FILE)
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
        df = df.dropna(subset=["Time"])
        df = df.sort_values("Time", ascending=False).reset_index(drop=True)
        return df
    except:
        # Auto-repair corrupted file
        st.warning("Fixing corrupted history file...")
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                lines = [l for l in f.readlines() if "," in l and not l.startswith("Time,PM2.5")]
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.write("Time,PM2.5\n")
                f.writelines(lines)
            df = pd.read_csv(HISTORY_FILE)
            df["Time"] = pd.to_datetime(df["Time"])
            return df.sort_values("Time", ascending=False)
        except:
            return pd.DataFrame(columns=["Time", "PM2.5"])

# ==================== FETCH PM2.5 ====================
def get_latest_pm25():
    try:
        API_KEY = "3b430ccb642b4f2f5cdc905c93d20a42054ceef85c7f7fe9f9b74f7ba8a5ebd9"
        response = requests.get(API_URL, headers={"X-API-Key": API_KEY})
        response.raise_for_status()
        r = response.json()["results"][0]
        return {
            "pm25": r["value"],
            "lat": r["coordinates"]["latitude"],
            "lon": r["coordinates"]["longitude"],
            "updated": r["datetime"]["local"],
            "location": "KLCC"
        }
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

if st.button("Refresh Data", type="primary"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("Fetching latest data..."):
    result = get_latest_pm25()

if not result:
    st.error("No data available")
    st.stop()

pm25 = result["pm25"]
lat = result["lat"]
lon = result["lon"]
updated_display = result["updated"]
location = result["location"]
time_str = updated_display[:16].replace("T", " ")

# Save to history
if save_reading(pm25, time_str):
    st.sidebar.success(f"New reading saved: {time_str}")

# AQI Color & Status
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

health_advice = {
    "Good": "Air quality is good. Enjoy outdoor activities.",
    "Moderate": "Sensitive groups should limit prolonged outdoor activity.",
    "Unhealthy for Sensitive Groups": "Limit outdoor activity and consider wearing a mask.",
    "Unhealthy": "Reduce outdoor exposure. Use masks if possible.",
    "Very Unhealthy": "Stay indoors. Avoid outdoor exercise."
}

# ==================== WEATHER ====================
def get_weather(lat, lon):
    try:
        API_KEY = "db9dd094e259767d649f772caaf17de5"
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        data = requests.get(url).json()
        return {
            "desc": data['weather'][0]['description'].title(),
            "temp": data['main']['temp'],
            "humidity": data['main']['humidity'],
            "wind": data['wind']['speed'],
            "rain": data.get('rain', {}).get('1h', 0)
        }
    except:
        return None

weather = get_weather(lat, lon)

# Weather-adjusted PM2.5
def expected_pm25(pm25, weather):
    modifier = 0
    if weather["wind"] >= 3: modifier -= 5
    elif weather["wind"] < 1: modifier += 5
    if weather["rain"] > 0: modifier -= 5
    adjusted = max(pm25 + modifier, 0)
    if adjusted <= 12: return adjusted, "Good"
    elif adjusted <= 35: return adjusted, "Moderate"
    elif adjusted <= 55: return adjusted, "Unhealthy for Sensitive Groups"
    elif adjusted <= 150: return adjusted, "Unhealthy"
    else: return adjusted, "Very Unhealthy"

def explain_pm25_change(weather):
    parts = []
    if weather["wind"] >= 3:
        parts.append("Windy conditions help disperse pollutants, lowering PM2.5.")
    elif weather["wind"] < 1:
        parts.append("Calm air allows pollutants to accumulate, increasing PM2.5.")
    if weather["rain"] > 0:
        parts.append("Rain washes particles from the air, reducing PM2.5.")
    return " ".join(parts) if parts else "Weather impact on PM2.5 is minimal at the moment."

if weather:
    adjusted_pm25, adjusted_status = expected_pm25(pm25, weather)
    explanation_text = explain_pm25_change(weather)
else:
    adjusted_pm25, adjusted_status = pm25, status
    explanation_text = ""
    weather = {"desc": "N/A", "temp": 0, "humidity": 0, "wind": 0, "rain": 0}

# ==================== SIDEBAR ====================
st.sidebar.success("Using REAL LIVE DATA from OpenAQ.")
st.sidebar.info("Data: OpenAQ v3 API (Clarity Node-S)\nUpdated every 10–30 minutes.")
history_df = load_history()
st.sidebar.metric("Total Saved Readings", len(history_df))

# ==================== MAIN LAYOUT ====================
col1, col2 = st.columns([1, 2])

with col1:
    st.metric("Original PM2.5", f"{pm25:.1f} µg/m³")
    st.metric("Expected PM2.5 (weather adjusted)", f"{adjusted_pm25:.1f} µg/m³")
    st.markdown(f"**Status (Expected PM2.5):** {adjusted_status}")
    st.info(health_advice[adjusted_status])
    st.caption(f"Location: {location}\n\nUpdated: {updated_display}")

with col2:
    m = folium.Map(location=[lat, lon], zoom_start=16, tiles="CartoDB positron")
    folium.CircleMarker(
        [lat, lon],
        radius=15,
        popup=f"{location}<br>Original: {pm25:.1f} → Expected: {adjusted_pm25:.1f} µg/m³<br>{updated_display}",
        tooltip=f"{adjusted_pm25:.1f} µg/m³",
        color="black", weight=3, fillColor=color, fillOpacity=0.9
    ).add_to(m)
    st_folium(m, width=700, height=400)

# ==================== WEATHER TABLE (EXACTLY LIKE app.py) ====================
st.markdown("### Weather Snapshot")
st.table({
    "Parameter": ["Description", "Temperature (°C)", "Humidity (%)", "Wind (m/s)", "Rain (mm)"],
    "Value": [
        weather['desc'],
        f"{weather['temp']:.1f}",
        f"{weather['humidity']}",
        f"{weather['wind']}",
        f"{weather['rain']}"
    ]
})

# Weather impact explanation
if explanation_text:
    st.markdown("### Weather Impact on PM2.5")
    st.markdown(explanation_text)

# ==================== HISTORY TABLE ====================
st.markdown("---")
st.subheader(f"All Saved Readings ({len(history_df)} total)")

if len(history_df) == 0:
    st.info("No historical data yet. Refresh a few times to collect readings!")
else:
    display = history_df.copy()
    display["Time"] = display["Time"].dt.strftime("%d %b %Y, %H:%M")
    display["PM2.5"] = display["PM2.5"].round(1)
    st.dataframe(display, use_container_width=True, hide_index=True)

st.success("Page loaded successfully.")
