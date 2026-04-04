"""
OpenWeatherMap integration — Free tier API for current weather + air pollution.
"""

import httpx
from config import get_settings

OWM_BASE = "https://api.openweathermap.org/data/2.5"


async def get_current_weather(lat: float, lng: float) -> dict:
    """Fetch current weather data for a location."""
    settings = get_settings()
    key = settings.openweathermap_api_key

    if not key:
        return _simulated_weather(lat, lng)

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            # Current weather
            weather_resp = await client.get(
                f"{OWM_BASE}/weather",
                params={"lat": lat, "lon": lng, "appid": key, "units": "metric"},
            )
            weather = weather_resp.json() if weather_resp.status_code == 200 else {}

            # Air pollution
            air_resp = await client.get(
                f"{OWM_BASE}/air_pollution",
                params={"lat": lat, "lon": lng, "appid": key},
            )
            air = air_resp.json() if air_resp.status_code == 200 else {}

            rain_1h = weather.get("rain", {}).get("1h", 0)
            temp = weather.get("main", {}).get("temp", 30)
            aqi_index = air.get("list", [{}])[0].get("main", {}).get("aqi", 1)
            # OWM AQI is 1-5 scale, convert to 0-500 scale
            aqi = {1: 50, 2: 100, 3: 200, 4: 300, 5: 400}.get(aqi_index, 100)

            return {
                "rainfall_mm_hr": rain_1h,
                "temperature_c": temp,
                "aqi": aqi,
                "humidity": weather.get("main", {}).get("humidity", 60),
                "wind_speed": weather.get("wind", {}).get("speed", 5),
                "description": weather.get("weather", [{}])[0].get("description", "clear"),
                "source": "openweathermap",
            }
        except Exception:
            return _simulated_weather(lat, lng)


def _simulated_weather(lat: float, lng: float) -> dict:
    """Fallback simulated weather data."""
    import random
    return {
        "rainfall_mm_hr": round(random.uniform(0, 15), 1),
        "temperature_c": round(random.uniform(25, 35), 1),
        "aqi": random.randint(50, 150),
        "humidity": random.randint(40, 80),
        "wind_speed": round(random.uniform(2, 12), 1),
        "description": random.choice(["clear sky", "few clouds", "light rain", "scattered clouds"]),
        "source": "simulated",
    }
