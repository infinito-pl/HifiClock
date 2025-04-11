import os
import json
import time
import requests
from config import WEATHER_API_KEY, WEATHER_UPDATE_INTERVAL, WEATHER_ICON_SIZE
from utils.logging import logger

def get_weather_data():
    """Pobiera dane pogodowe z OpenWeatherMap API."""
    try:
        # Najpierw pobierz lokalizację
        location_response = requests.get('http://ip-api.com/json/')
        location_data = location_response.json()
        city = location_data.get('city', 'Wroclaw')  # Domyślnie Wrocław

        # Następnie pobierz pogodę
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(weather_url)
        data = response.json()
        
        # Przetwórz dane
        result = {
            'temp': round(data['main']['temp']),
            'description': data['weather'][0]['description'].capitalize(),
            'icon': data['weather'][0]['icon'],
            'city': city
        }
        
        logger.debug(f"Weather data retrieved for {city}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting weather data: {e}")
        return None
