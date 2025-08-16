import streamlit as st
from geopy.geocoders import Nominatim
from astral import LocationInfo
from astral.sun import sun
import datetime
import pytz
from timezonefinder import TimezoneFinder  # Add timezone library

# Function to fetch sunrise time
def fetch_sunrise(place, date_obj):
    if not place:
        st.error("Please enter a location")
        return None
    if not date_obj:
        st.error("Please enter a valid date")
        return None
    
    try:
        geolocator = Nominatim(user_agent="hora_gui")
        location = geolocator.geocode(place)
        
        if not location:
            st.error("Location not found. Please try again.")
            return None
        
        lat = round(location.latitude, 6)
        lon = round(location.longitude, 6)
        
        # Using TimezoneFinder to get the timezone based on coordinates
        tz_finder = TimezoneFinder()
        timezone_str = tz_finder.timezone_at(lng=lon, lat=lat)
        tz = pytz.timezone(timezone_str) if timezone_str else pytz.utc
        
        city = LocationInfo(location.address, "Unknown", tz.zone, lat, lon)
        s = sun(city.observer, date=date_obj, tzinfo=tz)
        sunrise_time = s['sunrise'].strftime('%H:%M')
        
        return lat, lon, sunrise_time
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Streamlit UI
st.title("Sunrise Finder")

# Input Fields
place = st.text_input("Enter Location:")

# Use text_input to get DD-MM-YYYY format for date manually
date_str = st.text_input("Enter Date of Birth (DD-MM-YYYY):", value=datetime.date.today().strftime("%d-%m-%Y"))

# Function to convert the DD-MM-YYYY string into a date object
def convert_to_date(date_str):
    try:
        date_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
        return date_obj
    except ValueError:
        st.error("Invalid date format. Please use DD-MM-YYYY.")
        return None

# Convert the entered date string to a date object
date_obj = convert_to_date(date_str)

# Button to fetch sunrise time
if st.button("Get Sunrise"):
    result = fetch_sunrise(place, date_obj)
    
    if result:
        lat, lon, sunrise_time = result
        st.text(f"Date of Birth (formatted): {date_str}")  # Display the input date
        st.text(f"Latitude: {lat}")
        st.text(f"Longitude: {lon}")
        st.text(f"Sunrise (local time): {sunrise_time}")
