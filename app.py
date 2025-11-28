
import streamlit as st
import pandas as pd
import joblib
import folium
from streamlit_folium import st_folium

# Load the trained model
model = joblib.load('linear_regression_model.joblib')

st.title('Air Quality Prediction')

# Sidebar for user input
st.sidebar.header('Input Features')
feature1 = st.sidebar.slider('Feature 1', 0, 10, 5)
feature2 = st.sidebar.slider('Feature 2', 0, 10, 5)
feature3 = st.sidebar.slider('Feature 3', 0, 10, 5)

# Predict PM2.5
input_data = pd.DataFrame([[feature1, feature2, feature3]], columns=['feature1', 'feature2', 'feature3'])
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
