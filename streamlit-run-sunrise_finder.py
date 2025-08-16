import streamlit as st
import requests
import datetime
from geopy.geocoders import Nominatim
from astral import LocationInfo
from astral.sun import sun
from timezonefinder import TimezoneFinder
import pytz


# ---------------------------
# Function to fetch multiple location suggestions
# ---------------------------
def get_location_suggestions(query, country_hint=None):
    geolocator = Nominatim(user_agent="hora_gui")
    try:
        query_full = f"{query}, {country_hint}" if country_hint else query
        locations = geolocator.geocode(query_full, exactly_one=False, limit=5, addressdetails=True)
        return locations
    except Exception:
        return []


# ---------------------------
# Function to fetch sunrise
# ---------------------------
def fetch_sunrise(location_obj, date_obj):
    try:
        lat = round(location_obj.latitude, 6)
        lon = round(location_obj.longitude, 6)

        tz_finder = TimezoneFinder()
        timezone_str = tz_finder.timezone_at(lng=lon, lat=lat)

        if timezone_str:
            tz = pytz.timezone(timezone_str)
        else:
            st.warning("Timezone not found, defaulting to UTC.")
            tz = pytz.utc
            timezone_str = "UTC"

        city = LocationInfo(location_obj.address, "Unknown", timezone_str, lat, lon)
        s = sun(city.observer, date=date_obj, tzinfo=tz)
        sunrise_time = s['sunrise'].strftime('%H:%M')

        return lat, lon, sunrise_time, location_obj.address

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None


# ---------------------------
# Function to fetch user country
# ---------------------------
def get_user_country():
    try:
        ip = requests.get('https://api.ipify.org').text
        response = requests.get(f'https://ipinfo.io/{ip}/json')
        data = response.json()
        return data.get('country', 'Unknown')
    except:
        return 'Unknown'


# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Sunrise Finder", layout="centered")
st.title(":sunrise: Sunrise Finder")

# Get country hint
country = get_user_country()
st.text(f"Detected Country: {country}")

# Step 1: Enter location query
place_query = st.text_input("Enter Location (City, Place, Landmark):")

location_choice = None
locations = []

if place_query:
    locations = get_location_suggestions(place_query, country)
    if locations:
        options = [loc.address for loc in locations]
        choice = st.selectbox("Select the best match:", options)
        location_choice = next((loc for loc in locations if loc.address == choice), None)
    else:
        st.error("No matching locations found. Please refine your input.")

# Step 2: Enter date
date_str = st.text_input("Enter Date (DD-MM-YYYY):", value=datetime.date.today().strftime("%d-%m-%Y"))

def convert_to_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError:
        st.error("Invalid date format. Use DD-MM-YYYY.")
        return None

date_obj = convert_to_date(date_str)

# Step 3: Sunrise button
if st.button("Get Sunrise") and location_choice and date_obj:
    result = fetch_sunrise(location_choice, date_obj)
    if result:
        lat, lon, sunrise_time, resolved_address = result
        st.success(f":earth_asia: Location: {resolved_address}")
        st.text(f"Latitude: {lat}")
        st.text(f"Longitude: {lon}")
        st.text(f"Sunrise (local time): {sunrise_time}")
