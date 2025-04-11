import os
import json
import requests
import logging
from datetime import datetime
from config import WEATHER_API_KEY, ICONS_DIR

logger = logging.getLogger(__name__)

def get_city_from_ip():
    """Pobiera nazwę miasta na podstawie IP."""
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        data = response.json()
        return data.get("city", "")
    except Exception as e:
        logger.error(f"Błąd pobierania miasta z IP: {e}")
        return ""

def get_weather_data():
    """Pobiera dane pogodowe dla miasta."""
    try:
        city = get_city_from_ip()
        if not city:
            logger.error("Nie udało się pobrać nazwy miasta")
            return None

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()

        if response.status_code == 200:
            temp = round(data["main"]["temp"])
            icon_code = data["weather"][0]["icon"]
            icon_path = os.path.join(ICONS_DIR, f"{icon_code}.svg")
            
            logger.debug(f"Weather updated for {city}")
            return {
                "temp": temp,
                "icon": icon_code,
                "city": city
            }
        else:
            logger.error(f"Błąd API pogody: {data.get('message', 'Unknown error')}")
            return None

    except Exception as e:
        logger.error(f"Błąd pobierania pogody: {e}")
        return None
