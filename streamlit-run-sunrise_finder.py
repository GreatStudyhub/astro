import streamlit as st
import requests
import datetime
from geopy.geocoders import Nominatim
from astral import LocationInfo
from astral.sun import sun
from timezonefinder import TimezoneFinder
import pytz  # ✅ Fix: Import pytz

# ---------------------------
# Function to add Google Analytics with custom event tracking
# ---------------------------
def add_google_analytics(tracking_id):
    google_analytics_script = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={tracking_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{tracking_id}');
      
      // Custom function to send events
      function sendEvent(action, label="") {{
        gtag('event', action, {{
          'event_category': 'streamlit_app',
          'event_label': label
        }});
      }}
      window.sendEvent = sendEvent;
    </script>
    """
    st.components.v1.html(google_analytics_script, height=0)

# ---------------------------
# Function to fetch sunrise time
# ---------------------------
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
        
        # Get timezone from coordinates
        tz_finder = TimezoneFinder()
        timezone_str = tz_finder.timezone_at(lng=lon, lat=lat)
        
        if timezone_str:
            tz = pytz.timezone(timezone_str)
        else:
            st.warning("Timezone not found, defaulting to UTC.")
            tz = pytz.utc
            timezone_str = "UTC"
        
        city = LocationInfo(location.address, "Unknown", timezone_str, lat, lon)
        s = sun(city.observer, date=date_obj, tzinfo=tz)
        sunrise_time = s['sunrise'].strftime('%H:%M')
        
        return lat, lon, sunrise_time
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# ---------------------------
# Function to fetch the user's country based on IP
# ---------------------------
def get_user_country():
    try:
        ip = requests.get('https://api.ipify.org').text
        response = requests.get(f'https://ipinfo.io/{ip}/json')
        data = response.json()
        country = data.get('country', 'Unknown')
        return country
    except Exception as e:
        st.error(f"Could not retrieve country info: {e}")
        return 'Unknown'

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Location & Sunrise Finder", layout="centered")

# Add Google Analytics tracking
add_google_analytics("G-4SY4MKQMSJ")  # Replace with your GA4 ID

st.title("🌅 Location & Sunrise Finder")

# Show detected country
country = get_user_country()
st.text(f"Detected Country: {country}")

# Inputs
place = st.text_input("Enter Location:")
date_str = st.text_input("Enter Date of Birth (DD-MM-YYYY):", value=datetime.date.today().strftime("%d-%m-%Y"))

# Convert the DD-MM-YYYY string into a date object
def convert_to_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError:
        st.error("Invalid date format. Please use DD-MM-YYYY.")
        return None

date_obj = convert_to_date(date_str)

# Button: Fetch sunrise
if st.button("Get Sunrise"):
    # Fire GA event (custom)
    st.components.v1.html(
        f"<script>sendEvent('get_sunrise', '{place}');</script>", height=0
    )

    result = fetch_sunrise(place, date_obj)
    if result:
        lat, lon, sunrise_time = result
        st.text(f"Date of Birth (formatted): {date_str}")
        st.text(f"Latitude: {lat}")
        st.text(f"Longitude: {lon}")
        st.text(f"Sunrise (local time): {sunrise_time}")
