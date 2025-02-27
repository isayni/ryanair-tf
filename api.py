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

def get_round_trip_fares(args):
    params = {
        "currency": config.CURRENCY,
        "departureAirportIataCode": args.home_airports[0],
        "outboundDepartureDateFrom": args.date_min,
        "outboundDepartureDateTo": args.date_max,
        "inboundDepartureDateFrom": args.date_min,
        "inboundDepartureDateTo": args.date_max,
        "durationFrom": args.days_min,
        "durationTo": args.days_max,
        "adultPaxCount": args.passengers,
        "priceValueTo": args.price_max * args.passengers
    }
    if args.dest_country:
        params["arrivalCountryCode"] = args.dest_country
    elif args.dest_airports:
        params["arrivalAirportIataCodes"] = args.dest_airports

    data = requests.get(config.API_URL + "roundTripFares", params=params).json()
    return data['fares'] if 'fares' in data else []

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
        "inboundMonthOfDate": month,
    }
    return requests.get(
        config.API_URL + f"roundTripFares/{home_iata}/{dest_iata}/cheapestPerDay",
        params=params
    ).json()
