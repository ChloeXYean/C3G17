import streamlit as st
import pandas as pd
import joblib
import folium
from streamlit_folium import st_folium
import numpy as np

# Load the trained model
model = joblib.load('linear_regression_model.joblib')

st.title('Air Quality Prediction')

@st.cache_data(ttl=10)
def get_random_data():
    o3 = np.random.uniform(0, 10)
    so2 = np.random.uniform(0, 10)
    no2 = np.random.uniform(0, 10)
    return o3, so2, no2

# Get the cached random data
o3, so2, no2 = get_random_data()

st.sidebar.header('Randomly Generated Input')
st.sidebar.write(f"O3: {o3:.2f}")
st.sidebar.write(f"SO2: {so2:.2f}")
st.sidebar.write(f"NO2: {no2:.2f}")


# Predict PM2.5
# The model was trained with columns 'feature1', 'feature2', 'feature3'.
# We must use these column names for the prediction DataFrame.
input_data = pd.DataFrame([[o3, so2, no2]], columns=['feature1', 'feature2', 'feature3'])
prediction = model.predict(input_data)[0]

st.header(f'Predicted PM2.5: {prediction:.2f}')

st.subheader('Location Map')
# Create a map centered around Kuala Lumpur
m = folium.Map(location=[3.1390, 101.6869], zoom_start=11) # Centered on Kuala Lumpur

# Add a marker for the predicted location
folium.Marker(
    [3.1390, 101.6869],
    popup=f"Predicted PM2.5: {prediction:.2f}",
    tooltip='Kuala Lumpur'
).add_to(m)

# Display the map in the Streamlit app
st_folium(m, width=725)

st.write("The map is now centered on Kuala Lumpur, Malaysia.")
