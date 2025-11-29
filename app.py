
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.title('Air Quality')

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_latest_klcc_data():
    try:
        # Read the local CSV file
        df = pd.read_csv('klcc_data.csv')

        # Convert datetime string to datetime objects to find the most recent
        df['datetimeUtc'] = pd.to_datetime(df['datetimeUtc'])

        # Sort by datetime to find the latest entry
        latest_data = df.sort_values(by='datetimeUtc', ascending=False).iloc[0]

        # Extract the required values
        pm25 = latest_data['value']
        lat = latest_data['latitude']
        lon = latest_data['longitude']
        location_name = latest_data['location_name']
        unit = latest_data['unit']

        return pm25, lat, lon, location_name, unit
    except FileNotFoundError:
        st.error("The file 'klcc_data.csv' was not found.")
        st.stop()
    except Exception as e:
        st.error(f"Could not read or process klcc_data.csv: {e}")
        st.stop()

# Get the latest data from the CSV
pm25, lat, lon, location_name, unit = get_latest_klcc_data()

st.sidebar.header(f'Latest Data from {location_name}')
st.sidebar.write(f"PM2.5: {pm25:.2f} {unit}")

st.header(f'Latest PM2.5 at {location_name}: {pm25:.2f} {unit}')

st.subheader('Location Map')

# Create a map centered around the location from the data
m = folium.Map(location=[lat, lon], zoom_start=15)

# Add a marker for the location
folium.Marker(
    [lat, lon],
    popup=f"PM2.5: {pm25:.2f}",
    tooltip=location_name
).add_to(m)

# Display the map in the Streamlit app
st_folium(m, width=725)

st.write(f"Displaying the latest recorded PM2.5 value from your local klcc_data.csv file.")
