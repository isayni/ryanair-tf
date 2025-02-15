from functools import wraps
import requests
import config

request_count = 0

def count_requests(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global request_count
        request_count += 1
        return func(*args, **kwargs)
    return wrapper

requests.get = count_requests(requests.get)

def get_cheapest_flights(home_airports, date_min, date_max, price_max, dest_airports=None, dest_country=None):
    params = {
        "currency": config.CURRENCY,
        "departureAirportIataCodes": home_airports,
        "outboundDepartureDateFrom": date_min,
        "outboundDepartureDateTo": date_max,
        "priceValueTo": price_max
    }
    if dest_country:
        params["arrivalCountryCode"] = dest_country
    elif dest_airports:
        params["arrivalAirportIataCodes"] = dest_airports

    data = requests.get(config.API_URL + "oneWayFares", params=params).json()
    return [flight['outbound'] for flight in data['fares']] if 'fares' in data else []

def get_cheapest_per_day(home_iata, dest_iata, month):
    params = {
        "currency": config.CURRENCY,
        "outboundMonthOfDate": month,
    }
    data = requests.get(
        config.API_URL + f"oneWayFares/{home_iata}/{dest_iata}/cheapestPerDay",
        params=params
    ).json()
    return data['outbound']['fares'] if 'outbound' in data else []
