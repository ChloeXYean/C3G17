import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Interactive PM2.5 Map", layout="wide")
st.title("Interactive PM2.5 Air Quality Map & Health Risk")
API_KEY = "dc213ab59e72d5a2ad42b90957e9e531117bf633a774b6157751bae99dce8af6" 
API_URL = "https://api.openaq.org/v3/locations"


# ------------------- Helper functions -------------------    

data = requests.get(API_URL, params=params, timeout=10).json()
sensors = []
for loc in data.get("results", []):
    coords = loc.get("coordinates")
    latest = loc.get("latest", {})
    if coords and latest:
        sensors.append({
            "name": loc["name"],
            "pm25": round(latest.get("value", 0), 1),
            "lat": coords["latitude"],
            "lon": coords["longitude"],
            "updated": latest.get("date", {}).get("utc", "")[:16].replace("T", " ")
        })

def health_risk(pm25):
    if pm25 <= 12: return "Good", "green", "Safe for outdoor activity"
    if pm25 <= 35: return "Moderate", "yellow", "Sensitive groups reduce prolonged outdoor activity"
    if pm25 <= 55: return "Unhealthy for Sensitive Groups", "orange", "Children/elderly limit outdoor"
    if pm25 <= 150: return "Unhealthy", "red", "Everyone limit outdoor activity, wear mask"
    return "Very Unhealthy", "purple", "Stay indoors, use air purifier"

# ------------------- City Selection -------------------
city_list = ["Kuala Lumpur", "Petaling Jaya", "Shah Alam"]  # can expand with known cities
city = st.selectbox("Select a city:", city_list)

sensors = fetch_sensors(city)
if not sensors:
    st.warning("No real-time sensors found. Using demo data.")
    sensors = [
        {"name": "KLCC", "pm25": 28.5, "lat": 3.1564, "lon": 101.7098, "updated": "2025-11-29 12:00"},
        {"name": "Bangsar", "pm25": 42.1, "lat": 3.1300, "lon": 101.6700, "updated": "2025-11-29 11:55"},
    ]

# ------------------- Map -------------------
# Center map on average coordinates
avg_lat = sum(s["lat"] for s in sensors) / len(sensors)
avg_lon = sum(s["lon"] for s in sensors) / len(sensors)
m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles="CartoDB positron")

for s in sensors:
    risk, color, advice = health_risk(s["pm25"])
    folium.CircleMarker(
        [s["lat"], s["lon"]],
        radius=10,
        color="black",
        weight=2,
        fillColor=color,
        fillOpacity=0.8,
        tooltip=f"{s['name']}: {s['pm25']} µg/m³ → {risk}",
        popup=folium.Popup(
            f"<b>{s['name']}</b><br>PM2.5: {s['pm25']} µg/m³<br>Health: {risk}<br>Advice: {advice}<br>Updated: {s['updated']}",
            max_width=300
        )
    ).add_to(m)

# Render map
st_folium(m, width=1000, height=600)

# ------------------- Selected Sensor Info -------------------
st.markdown("### Sensor Details")
for s in sensors:
    st.write(f"**{s['name']}** — PM2.5: {s['pm25']} µg/m³ — Health: {health_risk(s['pm25'])[0]} — Updated: {s['updated']}")
