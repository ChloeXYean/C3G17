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


# ==================== HEALTH ADVICE ====================
health_advice = {
    "Good": "✅ Air quality is good. Enjoy outdoor activities.",
    "Moderate": "⚠ Sensitive groups should limit prolonged outdoor activity.",
    "Unhealthy for Sensitive Groups": "🟠 Limit outdoor activity and consider wearing a mask.",
    "Unhealthy": "🔴 Reduce outdoor exposure. Use masks if possible.",
    "Very Unhealthy": "🟣 Stay indoors. Avoid outdoor exercise."
}

# ====================  WEATHER SNAPSHOT  ====================
import requests

def get_weather(lat, lon):
    try:
        API_KEY = "db9dd094e259767d649f772caaf17de5"
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        weather_main = data['weather'][0]['main'].title()
        weather_desc = data['weather'][0]['description'].title()
        temp = data['main']['temp'] - 273.15 # Convert from Kelvin to Celsius
        humidity = data['main']['humidity']
        wind = data['wind']['speed']
        rain = data.get('rain', {}).get('1h', 0) 
        
        return {
            "main": weather_main,
            "desc": weather_desc,
            "temp": temp,
            "humidity": humidity,
            "wind": wind,
            "rain": rain
        }
    
    except:
        return None

# ==================== WEATHER + PM2.5 ======================
def expected_pm25(pm25, weather):
    """
    Calculate expected PM2.5 affected by weather conditions
    """
    wind = weather["wind"]
    rain = weather["rain"]
    
    # Wind modifier
    if wind >= 3:  # windy
        pm25_modifier = -5
    elif wind < 1:  # calm
        pm25_modifier = +5
    else:
        pm25_modifier = 0

    # Rain modifier
    if rain > 0:
        pm25_modifier -= 5

    adjusted_pm25 = max(pm25 + pm25_modifier, 0)
    
    # Determine AQI status
    if adjusted_pm25 <= 12:
        status = "Good"
    elif adjusted_pm25 <= 35:
        status = "Moderate"
    elif adjusted_pm25 <= 55:
        status = "Unhealthy for Sensitive Groups"
    elif adjusted_pm25 <= 150:
        status = "Unhealthy"
    else:
        status = "Very Unhealthy"
    
    return adjusted_pm25, status

    # ==================== FETCH WEATHER ====================
weather = get_weather(lat, lon)

if weather is None:
    st.warning("Weather data unavailable")
    weather_info = "N/A"
    adjusted_pm25, status = pm25, status
else:
    adjusted_pm25, status = expected_pm25(pm25, weather)
    weather_info = (
        f"{weather['desc']}\n"
        f"Temp: {weather['temp']:.1f}°C\n"
        f"Humidity: {weather['humidity']}%\n"
        f"Wind: {weather['wind']} m/s\n"
        f"Rain: {weather['rain']} mm"
    )

# ==================== EXPLAIN HOW WEATHER AFFECTS PM2.5 ====================
def explain_pm25_change(weather):
    explanations = []
    
    wind = weather["wind"]
    rain = weather["rain"]
    main = weather["main"]
    
    if wind >= 3:
        explanations.append("💨 Windy conditions help disperse pollutants, lowering PM2.5.")
    elif wind < 1:
        explanations.append("🫧 Calm air allows pollutants to accumulate, increasing PM2.5.")
    
    if rain > 0:
        explanations.append(f"💧 Rain washes particles from the air, reducing PM2.5 by approximately {rain} mm rain.")

    if not explanations:
        explanations.append("Weather impact on PM2.5 is minimal at the moment.")
    
    return " ".join(explanations)

# ==================== SIDEBAR INDICATOR ====================
st.sidebar.success("🟢 Using REAL LIVE DATA from OpenAQ.")
st.sidebar.info("Data: OpenAQ v3 API (Clarity Node-S)\nUpdated every 10–30 minutes.")

# ==================== DISPLAY INFO ====================
col1, col2 = st.columns([1, 2])

with col1:
    # Fetch weather
    weather = get_weather(lat, lon)
    
    if weather:
        adjusted_pm25, status = expected_pm25(pm25, weather)
        explanation_text = explain_pm25_change(weather)

    else:
        adjusted_pm25, status = pm25, status
        explanation_text = ""
        weather_info = "Weather data unavailable"
    
    # Display PM2.5 metrics
    st.metric("Original PM2.5", f"{pm25:.1f} µg/m³")
    st.metric("Expected PM2.5 (weather adjusted)", f"{adjusted_pm25:.1f} µg/m³")
    st.markdown(f"**Status (Expected PM2.5):** {status}")
    st.info(health_advice[status])
    st.caption(f"Location: {location}\nUpdated: {updated_display}")

with col2:
    m = folium.Map(location=[lat, lon], zoom_start=16, tiles="CartoDB positron")
    folium.CircleMarker(
        [lat, lon],
        radius=15,
        popup=(
            f"{location}<br>"
            f"Original PM2.5: {pm25:.1f} µg/m³<br>"
            f"Expected PM2.5: {adjusted_pm25:.1f} µg/m³<br>"
            f"Updated: {updated_display}"
        ),
        tooltip=f"{pm25} µg/m³",
        color="black",
        weight=3,
        fillColor=color,
        fillOpacity=0.9
    ).add_to(m)
    st_folium(m, width=700, height=400)


st.markdown("### ⛅ Weather Snapshot")
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
    
# Display explanation
if explanation_text:
    st.markdown("### Weather Impact on PM2.5")
    st.markdown(explanation_text)

st.success("✓ Page loaded successfully.")