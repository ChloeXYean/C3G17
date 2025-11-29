import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

API_KEY = "dc213ab59e72d5a2ad42b90957e9e531117bf633a774b6157751bae99dce8af6"
BASE_URL = "https://api.openaq.org/v3"

headers = {"X-API-Key": API_KEY}


# -----------------------------------------------------------
# Fetch Country List
# -----------------------------------------------------------
def fetch_countries():
    try:
        url = f"{BASE_URL}/countries"
        r = requests.get(url, headers=headers)
        data = r.json()

        if "results" not in data:
            return []

        countries = {c["code"]: c["name"] for c in data["results"]}
        return countries

    except Exception as e:
        st.error(f"Country API Error: {e}")
        return []


# -----------------------------------------------------------
# Fetch Locations (Sensors) for country
# -----------------------------------------------------------
def fetch_locations(country_code):
    try:
        url = f"{BASE_URL}/locations?country={country_code}"
        r = requests.get(url, headers=headers)
        data = r.json()

        if "results" not in data:
            return []

        return data["results"]

    except Exception as e:
        st.error(f"Location API Error: {e}")
        return []


# -----------------------------------------------------------
# Fetch latest PM25 measurement
# -----------------------------------------------------------
def get_latest_pm25(location_id):
    try:
        url = f"{BASE_URL}/measurements?location_id={location_id}&parameter=pm25&limit=1"
        r = requests.get(url, headers=headers)
        data = r.json()

        if "results" not in data or len(data["results"]) == 0:
            return None
        
        rec = data["results"][0]

        return {
            "pm25": rec.get("value"),
            "lat": rec["coordinates"]["latitude"],
            "lon": rec["coordinates"]["longitude"],
            "updated": rec["date"]["local"],
        }

    except Exception as e:
        st.error(f"PM2.5 Error: {e}")
        return None


# -----------------------------------------------------------
# STREAMLIT UI
# -----------------------------------------------------------
st.title("🌍 Real-time Air Quality (OpenAQ API v3)")
st.write("Live country → location → PM2.5 dashboard")

# 1️⃣ Load countries
st.subheader("Step 1: Choose Country")
countries = fetch_countries()

if not countries:
    st.error("No countries found!")
    st.stop()

selected_country = st.selectbox("Country", list(countries.keys()), format_func=lambda c: countries[c])

# 2️⃣ Load sensors for selected country
st.subheader("Step 2: Choose Monitoring Location")
locations = fetch_locations(selected_country)

if not locations:
    st.warning("No sensors available for this country.")
    st.stop()

loc_dict = {loc["id"]: loc["name"] for loc in locations}
selected_location_id = st.selectbox("Location", list(loc_dict.keys()), format_func=lambda i: loc_dict[i])

# 3️⃣ Get PM25
st.subheader("Step 3: Latest PM2.5 Reading")
pm25_data = get_latest_pm25(selected_location_id)

if pm25_data is None:
    st.warning("No PM2.5 data available for this location.")
    st.stop()

st.metric("PM2.5", f"{pm25_data['pm25']} µg/m³")
st.write(f"Updated: {pm25_data['updated']}")

# 4️⃣ Map
st.subheader("Map Visualization")

m = folium.Map(location=[pm25_data["lat"], pm25_data["lon"]], zoom_start=13)

folium.Marker(
    [pm25_data["lat"], pm25_data["lon"]],
    popup=f"PM2.5: {pm25_data['pm25']}"
).add_to(m)

st_folium(m, height=400)
