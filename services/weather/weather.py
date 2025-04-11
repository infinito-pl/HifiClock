import os
import json
import time
import requests
from config import WEATHER_CACHE_DIR, WEATHER_CACHE_TIME, OPENWEATHER_API_KEY
from utils.logging import logger

def get_city_from_ip():
    """Pobiera nazwę miasta na podstawie adresu IP."""
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('city', 'Warsaw')  # Domyślnie Warszawa
    except Exception as e:
        logger.error(f"Błąd pobierania miasta: {e}")
    return 'Warsaw'  # Domyślne miasto w przypadku błędu

def get_weather_data():
    """Pobiera dane pogodowe z OpenWeatherMap API."""
    try:
        # Sprawdź cache
        cache_file = os.path.join(WEATHER_CACHE_DIR, 'weather.json')
        if os.path.exists(cache_file):
            cache_time = os.path.getmtime(cache_file)
            if time.time() - cache_time < WEATHER_CACHE_TIME:
                with open(cache_file, 'r') as f:
                    return json.load(f)

        # Pobierz miasto
        city = get_city_from_ip()
        
        # Sprawdź czy mamy klucz API
        if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "twój_klucz_api":
            logger.error("Brak poprawnego klucza API OpenWeather w config.py")
            return None
            
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            logger.error(f"Błąd API OpenWeather: {response.status_code}")
            return None
            
        data = response.json()
        
        # Przygotuj dane do zwrócenia
        weather_data = {
            'temp': round(data['main']['temp']),
            'icon': data['weather'][0]['icon'],
            'description': data['weather'][0]['description'],
            'city': city
        }
        
        # Zapisz do cache
        os.makedirs(WEATHER_CACHE_DIR, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(weather_data, f)
            
        return weather_data
        
    except Exception as e:
        logger.error(f"Błąd pobierania danych pogodowych: {e}")
        return None
