# sunrise_panchang.py
import streamlit as st
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from astral import LocationInfo
from astral.sun import sun
import pytz
import datetime
import swisseph as swe  # pyswisseph
import math

# ----------------------------
# Helper: location suggestions
# ----------------------------
def get_location_suggestions(query, country_hint=None):
    geolocator = Nominatim(user_agent="hora_gui", timeout=10)
    try:
        country_map = {
            "India":"IN","United States":"US","United Kingdom":"GB","Canada":"CA",
            "Australia":"AU","Singapore":"SG","UAE":"AE","Germany":"DE","France":"FR"
        }
        country_code = country_map.get(country_hint, None)
        q = f"{query}, {country_hint}" if country_hint and country_hint != "Other" else query
        locations = geolocator.geocode(q, exactly_one=False, limit=6, addressdetails=True, country_codes=country_code)
        return locations or []
    except Exception as e:
        st.warning(f"Geocoding issue: {e}")
        return []

# ----------------------------
# Astronomy helpers (swisseph)
# ----------------------------
# Zodiac & Nakshatra names
ZODIAC = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
NAKSHATRA = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
    "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
    "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Moola","Purva Ashadha",
    "Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
    "Uttara Bhadrapada","Revati"
]

# Convert local time -> UTC julian day UT for swisseph
def datetime_to_julday_utc(dt_local, tz):
    # dt_local: naive or tz-aware local datetime
    if dt_local.tzinfo is None:
        local = tz.localize(dt_local)
    else:
        local = dt_local.astimezone(tz)
    dt_utc = local.astimezone(pytz.utc)
    year = dt_utc.year
    month = dt_utc.month
    day = dt_utc.day
    hour = dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0 + dt_utc.microsecond/(3600.0*1e6)
    jd = swe.julday(year, month, day, hour)
    return jd

# Normalize angle to 0-360
def norm(angle):
    a = angle % 360.0
    if a < 0:
        a += 360.0
    return a

def deg_to_sign(long_deg):
    sign = int(long_deg // 30)  # 0..11
    deg_in_sign = long_deg % 30
    return ZODIAC[sign], sign+1, deg_in_sign  # sign name, sign number 1..12, degrees in sign

def calc_nakshatra_and_pada(long_deg):
    # total 360 deg divided into 27 nakshatras -> each 13 1/3 deg = 360/27
    nak_size = 360.0 / 27.0  # 13.333...
    pada_size = nak_size / 4.0  # 3.333...
    idx = int(long_deg // nak_size)  # 0..26
    nak = NAKSHATRA[idx]
    deg_into_nak = long_deg - (idx * nak_size)
    pada = int(deg_into_nak // pada_size) + 1  # 1..4
    return idx+1, nak, pada, deg_into_nak  # nakshatra number (1..27), name, pada, degrees into nak

def compute_house(planet_long, asc_long):
    # Houses are 30-degree slices starting from ascendant
    rel = (planet_long - asc_long) % 360.0
    house = int(rel // 30.0) + 1  # house 1..12
    deg_in_house = rel % 30.0
    return house, deg_in_house

# ----------------------------
# Primary logic: sunrise + positions
# ----------------------------
def fetch_sunrise_and_positions(location_obj, date_obj):
    try:
        lat = round(location_obj.latitude, 6)
        lon = round(location_obj.longitude, 6)

        tz_finder = TimezoneFinder()
        tz_str = tz_finder.timezone_at(lng=lon, lat=lat)
        if tz_str:
            tz = pytz.timezone(tz_str)
        else:
            tz = pytz.utc
            tz_str = "UTC"

        # get sunrise time using astral
        city_short = location_obj.address.split(",")[0]
        city = LocationInfo(city_short, "", tz_str, lat, lon)
        s = sun(city.observer, date=date_obj, tzinfo=tz)
        sunrise_dt_local = s["sunrise"]  # timezone-aware

        # convert to julian day UT for swisseph (needs UT)
        jd_ut = datetime_to_julday_utc(sunrise_dt_local, tz)

        # ensure ephemeris
        # (optionally set a path: swe.set_ephe_path("/path/to/ephe") )
        swe.set_ephe_path('.')  # current directory try; swisseph uses internal if not found

        # Compute ascendant (house cusps)
        # swe.houses(jd_ut, lat, lon, hsys='P') returns (cusps, ascmc) where ascmc[0] is ascendant
        cusps, ascmc = swe.houses(jd_ut, lat, lon, hsys='P')  # Placidus
        ascendant = norm(ascmc[0])  # degrees

        # Planetary longitudes (ecliptic)
        sun_ecl = norm(swe.calc_ut(jd_ut, swe.SUN)[0][0])  # returns (lon, lat, dist)
        moon_ecl = norm(swe.calc_ut(jd_ut, swe.MOON)[0][0])

        # Sun details
        sun_sign, sun_sign_no, sun_deg_in_sign = deg_to_sign(sun_ecl)
        sun_nak_no, sun_nak_name, sun_pada, sun_deg_into_nak = calc_nakshatra_and_pada(sun_ecl)
        sun_house, sun_deg_in_house = compute_house(sun_ecl, ascendant)

        # Moon details
        moon_sign, moon_sign_no, moon_deg_in_sign = deg_to_sign(moon_ecl)
        moon_nak_no, moon_nak_name, moon_pada, moon_deg_into_nak = calc_nakshatra_and_pada(moon_ecl)
        moon_house, moon_deg_in_house = compute_house(moon_ecl, ascendant)

        out = {
            "latitude": lat,
            "longitude": lon,
            "timezone": tz_str,
            "sunrise_local": sunrise_dt_local,
            "jd_ut": jd_ut,
            "ascendant_deg": ascendant,
            "sun": {
                "ecliptic_long": sun_ecl,
                "sign": sun_sign,
                "sign_no": sun_sign_no,
                "deg_in_sign": sun_deg_in_sign,
                "nakshatra_no": sun_nak_no,
                "nakshatra": sun_nak_name,
                "pada": sun_pada,
                "deg_into_nak": sun_deg_into_nak,
                "house": sun_house,
                "deg_in_house": sun_deg_in_house
            },
            "moon": {
                "ecliptic_long": moon_ecl,
                "sign": moon_sign,
                "sign_no": moon_sign_no,
                "deg_in_sign": moon_deg_in_sign,
                "nakshatra_no": moon_nak_no,
                "nakshatra": moon_nak_name,
                "pada": moon_pada,
                "deg_into_nak": moon_deg_into_nak,
                "house": moon_house,
                "deg_in_house": moon_deg_in_house
            }
        }

        return out

    except Exception as e:
        st.error(f"Error computing positions: {e}")
        return None

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Sunrise + Sun/Moon Panchang", layout="centered")
st.title("Sunrise + Sun & Moon: Sign, Nakshatra, Patham (Pada) & House")

country_list = ["India", "United States", "United Kingdom", "Canada", "Australia", "Singapore", "UAE", "Germany", "France", "Other"]
country = st.selectbox("Select Your Country:", country_list, index=0)

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

date_str = st.text_input("Enter Date (DD-MM-YYYY):", value=datetime.date.today().strftime("%d-%m-%Y"))

def convert_to_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError:
        st.error("Invalid date format. Use DD-MM-YYYY.")
        return None

date_obj = convert_to_date(date_str)

if st.button("Get Sunrise & Positions") and location_choice and date_obj:
    data = fetch_sunrise_and_positions(location_choice, date_obj)
    if data:
        st.success(f"Location: {location_choice.address}")
        st.write(f"Latitude: {data['latitude']}, Longitude: {data['longitude']}")
        st.write(f"Timezone: {data['timezone']}")
        st.write(f"Sunrise (local): {data['sunrise_local'].strftime('%Y-%m-%d %H:%M:%S %Z')}")

        st.subheader("Ascendant (Lagna)")
        asc_sign, asc_sign_no, asc_deg_in_sign = deg_to_sign(data['ascendant_deg'])
        st.write(f"Ascendant: {asc_sign} ({round(data['ascendant_deg'],3)}°) — Sign number {asc_sign_no}, {round(asc_deg_in_sign,3)}° into sign")

        st.subheader("Sun at Sunrise")
        sun = data['sun']
        st.write(f"Ecliptic Longitude: {round(sun['ecliptic_long'],4)}°")
        st.write(f"Sign: {sun['sign']} (#{sun['sign_no']}) — {round(sun['deg_in_sign'],4)}° in sign")
        st.write(f"Nakshatra: {sun['nakshatra']} (#{sun['nakshatra_no']}) — Pada/Patham: {sun['pada']} — {round(sun['deg_into_nak'],4)}° into nakshatra")
        st.write(f"House (from Ascendant): {sun['house']} — {round(sun['deg_in_house'],4)}° into that house")

        st.subheader("Moon at Sunrise")
        moon = data['moon']
        st.write(f"Ecliptic Longitude: {round(moon['ecliptic_long'],4)}°")
        st.write(f"Sign: {moon['sign']} (#{moon['sign_no']}) — {round(moon['deg_in_sign'],4)}° in sign")
        st.write(f"Nakshatra: {moon['nakshatra']} (#{moon['nakshatra_no']}) — Pada/Patham: {moon['pada']} — {round(moon['deg_into_nak'],4)}° into nakshatra")
        st.write(f"House (from Ascendant): {moon['house']} — {round(moon['deg_in_house'],4)}° into that house")

        # small map and raw output
        st.map({'lat':[data['latitude']],'lon':[data['longitude']]})
        st.write("---")
        st.write("Raw data (for debugging):")
        st.json(data)
    else:
        st.error("Failed to compute positions.")
