import os
import urllib.parse
import urllib.request
import json

DEFAULT_CITY = os.getenv("JARVIS_CITY", "Guntur")

# Pre-cached coordinates for fast lookup of Indian cities, fallback to Open-Meteo Geocoding
CITY_COORDS = {
    "guntur": (16.3067, 80.4365, "Guntur", "Andhra Pradesh"),
    "vijayawada": (16.5062, 80.6480, "Vijayawada", "Andhra Pradesh"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad", "Telangana"),
    "bangalore": (12.9716, 77.5946, "Bengaluru", "Karnataka"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru", "Karnataka"),
    "chennai": (13.0827, 80.2707, "Chennai", "Tamil Nadu"),
    "mumbai": (19.0760, 72.8777, "Mumbai", "Maharashtra"),
    "delhi": (28.6139, 77.2090, "Delhi", "Delhi")
}

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm"
}

def resolve_coordinates(city_name: str):
    key = city_name.strip().lower()
    if key in CITY_COORDS:
        return CITY_COORDS[key]
        
    try:
        query = urllib.parse.quote(city_name)
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1&language=en&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/2.2"})
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            if "results" in data and data["results"]:
                res_data = data["results"][0]
                lat = res_data.get("latitude")
                lon = res_data.get("longitude")
                name = res_data.get("name", city_name)
                country = res_data.get("country", "")
                return lat, lon, name, country
    except Exception:
        pass
    # Default to Guntur
    return 16.3067, 80.4365, "Guntur", "Andhra Pradesh"

def fetch_open_meteo_weather(city: str = ""):
    location = (city or DEFAULT_CITY).strip()
    lat, lon, place, region = resolve_coordinates(location)
    
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,"
        f"apparent_temperature,weather_code,wind_speed_10m&timezone=auto"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/2.2"})
    with urllib.request.urlopen(req, timeout=6) as res:
        data = json.loads(res.read().decode("utf-8"))
        current = data.get("current", {})
        
        temp_c = round(current.get("temperature_2m", 0), 1)
        feels_like = round(current.get("apparent_temperature", temp_c), 1)
        humidity = current.get("relative_humidity_2m", 0)
        wind = current.get("wind_speed_10m", 0)
        code = current.get("weather_code", 0)
        desc = WEATHER_CODES.get(code, "Partly cloudy")
        
        return {
            "place": place,
            "region": region,
            "temp_c": temp_c,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind": wind,
            "desc": desc
        }

def get_weather(city: str = "") -> str:
    """Returns current weather and temperature for a city using live high-precision satellite data."""
    try:
        w = fetch_open_meteo_weather(city)
        temp_f = round((w["temp_c"] * 9/5) + 32, 1)
        return (
            f"Live weather for {w['place']}, {w['region']}: {w['desc']}. "
            f"Temperature is {w['temp_c']} degrees Celsius ({temp_f} Fahrenheit). "
            f"Feels like {w['feels_like']} degrees Celsius. Humidity is {w['humidity']} percent. "
            f"Wind speed is {w['wind']} kilometers per hour."
        )
    except Exception as exc:
        return f"I could not fetch live weather right now. Error: {exc}"

def get_weather_dict(city: str = "") -> dict:
    """Returns a parsed dictionary of weather parameters for GUI telemetry cards."""
    try:
        w = fetch_open_meteo_weather(city)
        return {"place": w["place"], "temp_c": f"{int(round(w['temp_c']))}", "desc": w["desc"]}
    except Exception:
        return {"place": city or DEFAULT_CITY, "temp_c": "N/A", "desc": "Unknown"}
