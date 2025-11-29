import streamlit as st
import requests

api_key = st.secrets["OPENAQ_API_KEY"]

url = "https://api.openaq.org/v3/locations?country=MY&parameter=pm25&limit=1"
headers = {"X-API-Key": api_key}

resp = requests.get(url, headers=headers).json()

print(resp)  # Check the JSON response
