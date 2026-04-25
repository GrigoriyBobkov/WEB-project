import requests
import math

STATIC_API_KEY = '0ae0d0c4-5544-4343-8056-805047179144'
GEOCODER_API_KEY = '8013b162-6b42-4997-9691-77b7074026e0'

def get_coordinates(city_name):
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": city_name,
        "format": "json"
    }

    try:
        response = requests.get(url, params, timeout=10)
        data = response.json()

        feature_member = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
        if not feature_member:
            print(f"Город {city_name} не найден")
            return None, None

        point = feature_member[0]['GeoObject']['Point']['pos']
        lon, lat = point.split()
        print(f"Город {city_name} найден: {lon}, {lat}")
        return float(lon), float(lat)

    except Exception as e:
        print(f"Ошибка геокодирования: {e}")
        return None, None

def get_static_map(lon, lat, zoom=15, width=650, height=450):
    spn = 0.1 / (2 ** ((zoom - 10) / 2))

    if spn < 0.0005:
        spn = 0.0005
    if spn > 0.1:
        spn = 0.1

    url = f"https://static-maps.yandex.ru/v1?ll={lon},{lat}&spn={spn},{spn}&size={width},{height}&apikey={STATIC_API_KEY}"
    print(f"Карта URL (zoom={zoom}, spn={spn:.6f}): {url}")
    return url