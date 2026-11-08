from datetime import datetime

import requests


def get_current_time() -> str:
    return f"Currently, it is {datetime.now().strftime('%H:%M:%S')}."

def get_weather(city: str, *, api_key: str) -> str:
    city = city.strip()

    if not city:
        raise ValueError("Le nom de la ville est vide.")

    if not api_key.strip():
        raise ValueError("La clé météo est vide.")

    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key": api_key,
        "q": city
    }

    response = requests.get(
        url,
        params=params,
        timeout=(3.0,30.0)
    )
    response.raise_for_status()

    data = response.json()
    temperature = data["current"]["temp_c"]

    return f"Currently, the temperature in {city} is {temperature}°C."