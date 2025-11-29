import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
import os

st.set_page_config(page_title="KLCC PM2.5", layout="centered")
st.title("KLCC Kuala Lumpur")
st.markdown("### Real-time PM2.5 Air Quality")

API_URL = "https://api.openaq.org/v3/locations/5893160/latest"
API_KEY = "dc213ab59e72d5a2ad42b90957e9e531117bf633a774b6157751bae99dce8af6"
HISTORY_FILE = "pm25_history.csv"

# === GET LIVE DATA ===
def get_latest():
    try:
        r = requests.get(API_URL, headers={"X-API-Key": API_KEY})
        data = r.json()["results"][0]
        return {
            "pm25": data["value"],
            "time": data["datetime"]["local"][:16].replace("T", " ")
        }
    except:
        st.error("Cannot connect to sensor")
        return None

# === SAVE TO CSV (only if time is new) ===
def save(pm25, time_str):
    line = f"{time_str},{pm25}\n"
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            f.write("Time,PM2.5\n")
    
    # Check if this time already exists
    try:
        with open(HISTORY_FILE, "r") as f:
            content = f.read()
            if time_str in content:
                return False
    except:
        pass
    
    with open(HISTORY_FILE, "a") as f:
        f.write(line)
    return True

# === LOAD HISTORY ===
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["Time", "PM2.5"])
    df = pd.read_csv(HISTORY_FILE)
    df["Time"] = pd.to_datetime(df["Time"])
    df = df.sort_values("Time", ascending=False)  # newest first
    return df

# === MAIN ===
data = get_latest()
if not data:
    st.stop()

pm25 = data["pm25"]
time_now = data["time"]

# Save only if this exact time doesn't exist
if save(pm25, time_now):
    st.success(f"Saved: {time_now}")

# Load all history
history = load_history()

# AQI Color
def color(pm):
    if pm <= 12:  return "green"
    if pm <= 35:  return "yellow"
    if pm <= 55:  return "orange"
    if pm <= 150: return "red"
    return "purple"

# === DISPLAY ===
col1, col2 = st.columns([1, 2])
with col1:
    st.metric("PM2.5", f"{pm25:.1f} µg/m³")
    st.markdown(f"<h2 style='color:{color(pm25)}'>● Live Now</h2>", unsafe_allow_html=True)
    st.caption(f"Updated: {time_now}")

with col2:
    m = folium.Map(location=[3.1579, 101.7123], zoom_start=16, tiles="CartoDB positron")
    folium.CircleMarker(
        [3.1579, 101.7123],
        radius=20, color="black", fillColor=color(pm25), fillOpacity=0.9,
        popup=f"PM2.5: {pm25:.1f}<br>{time_now}"
    ).add_to(m)
    st_folium(m, height=400)

if st.button("Refresh", type="primary"):
    st.rerun()

st.markdown("---")
st.subheader(f"All Readings ({len(history)} total)")

if len(history) == 0:
    st.info("No data yet. Refresh a few times!")
else:
    # Show nice table
    display = history.copy()
    display["Time"] = display["Time"].dt.strftime("%d %b %Y, %H:%M")
    display["PM2.5"] = display["PM2.5"].round(1)
    st.dataframe(display, use_container_width=True, hide_index=True)

st.sidebar.success(f"Total saved: {len(history)} readings")
if len(history) > 0:
    st.sidebar.caption(f"First: {history['Time'].iloc[-1].strftime('%d %b %H:%M')}")