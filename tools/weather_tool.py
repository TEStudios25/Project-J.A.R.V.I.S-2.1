import os
import urllib.parse
import urllib.request

DEFAULT_CITY = os.getenv("JARVIS_CITY", "Guntur")


def get_weather(city: str = "") -> str:
    """Returns current weather and temperature for a city using live web data."""
    location = (city or DEFAULT_CITY).strip()
    print(f"\n[🌤️ J.A.R.V.I.S. is checking weather for {location}...]")

    try:
        query = urllib.parse.quote(location)
        url = f"https://wttr.in/{query}?format=j1"
        request = urllib.request.Request(url, headers={"User-Agent": "Project-JARVIS/2.0"})
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = response.read().decode("utf-8")

        import json

        data = json.loads(payload)
        current = data["current_condition"][0]
        area = data["nearest_area"][0]
        place = area["areaName"][0]["value"]
        region = area["country"][0]["value"]
        temp_c = current.get("temp_C", "N/A")
        temp_f = current.get("temp_F", "N/A")
        feels_like = current.get("FeelsLikeC", "N/A")
        humidity = current.get("humidity", "N/A")
        wind = current.get("windspeedKmph", "N/A")
        desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")

        return (
            f"Live weather for {place}, {region}: {desc}. "
            f"Temperature is {temp_c} degrees Celsius, {temp_f} Fahrenheit. "
            f"Feels like {feels_like} Celsius. Humidity {humidity} percent. "
            f"Wind speed {wind} kilometers per hour."
        )
    except Exception as exc:
        return f"I could not fetch live weather right now. Error: {exc}"

def get_weather_dict(city: str = "") -> dict:
    """Returns a parsed dictionary of weather parameters for GUI telemetry cards."""
    location = (city or DEFAULT_CITY).strip()
    try:
        query = urllib.parse.quote(location)
        url = f"https://wttr.in/{query}?format=j1"
        request = urllib.request.Request(url, headers={"User-Agent": "Project-JARVIS/2.0"})
        with urllib.request.urlopen(request, timeout=6) as response:
            payload = response.read().decode("utf-8")
        
        import json
        data = json.loads(payload)
        current = data["current_condition"][0]
        area = data["nearest_area"][0]
        place = area["areaName"][0]["value"]
        temp_c = current.get("temp_C", "N/A")
        desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
        return {"place": place, "temp_c": temp_c, "desc": desc}
    except Exception:
        return {"place": location, "temp_c": "N/A", "desc": "Unknown"}
