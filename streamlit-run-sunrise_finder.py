import streamlit as st
from geopy.geocoders import Nominatim
from astral import LocationInfo
from astral.sun import sun
import datetime
import pytz

# Function to fetch sunrise time
def fetch_sunrise(place, date_str):
    if not place:
        st.error("Please enter a location")
        return None
    if not date_str:
        st.error("Please enter a date in YYYY-MM-DD format")
        return None
    
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        st.error("Invalid date format. Use YYYY-MM-DD")
        return None
    
    try:
        geolocator = Nominatim(user_agent="hora_gui")
        location = geolocator.geocode(place)
        
        if not location:
            st.error("Location not found. Please try again.")
            return None
        
        lat = round(location.latitude, 6)
        lon = round(location.longitude, 6)
        
        # Guess timezone (basic)
        try:
            tz = pytz.timezone("Asia/Kolkata") if "India" in location.address else pytz.utc
        except:
            tz = pytz.utc
        
        city = LocationInfo(location.address, "Unknown", tz.zone, lat, lon)
        s = sun(city.observer, date=date_obj, tzinfo=tz)
        sunrise_time = s['sunrise'].strftime('%H:%M')
        
        return lat, lon, sunrise_time
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Streamlit UI
st.title("Location & Sunrise Finder")

# Input Fields
place = st.text_input("Enter Location:")
date_str = st.text_input("Enter Date (YYYY-MM-DD):", value=datetime.date.today().strftime("%Y-%m-%d"))

# Button to fetch sunrise time
if st.button("Get Sunrise"):
    result = fetch_sunrise(place, date_str)
    
    if result:
        lat, lon, sunrise_time = result
        st.text(f"Latitude: {lat}")
        st.text(f"Longitude: {lon}")
        st.text(f"Sunrise (local time): {sunrise_time}")