import streamlit as st
import requests
import folium
from streamlit_folium import st_folium


@st.cache_data(ttl=180)
def fetch_sensors(city):
    """Fetch all PM2.5 sensors in a city from OpenAQ."""
    try:

        response = requests.get(
            API_URL,
            headers={"X-API-Key": API_KEY}
        )
        response.raise_for_status()
        return {
            "city": city,
            "parameter_id": 2,  # PM2.5
            "limit": 100,        # fetch up to 100 sensors
            "sort": "desc",
            "order_by": "lastUpdated"
        }
    
    except Exception as e:
        st.error(f"Error fetching API: {e}")
        return None