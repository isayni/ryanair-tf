from datetime import datetime, timedelta
from functools import wraps
import requests
import config
from utils import add_days_to_date, get_months_between, enrich_fare_info, create_trip

request_count = 0

def count_requests(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global request_count
        request_count += 1
        return func(*args, **kwargs)
    return wrapper

requests.get = count_requests(requests.get)

def get_cheapest_fares(params):
    data = requests.get(config.API_URL + "oneWayFares", params=params).json()
    return [fare['outbound'] for fare in data['fares']] if 'fares' in data else []

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

def find_alternative_fares(fare, datetime_min, datetime_max, price_max):
    '''
        find suitable alternatives for a specific fare
    '''
    def fares_filter(fare, datetime_min, datetime_max, price_max):
        datetime_min.replace(hour=0)
        datetime_max.replace(hour=23, minute=59)

        if fare['price'] is None or fare['price']['value'] > price_max:
            return False

        datetime_flight = datetime.fromisoformat(fare['departureDate'])

        if datetime_flight < datetime_min or datetime_flight > datetime_max:
            return False

        return True

    home_iata = fare['departureAirport']['iataCode']
    home_city = fare['departureAirport']['city']['name']
    dest_iata = fare['arrivalAirport']['iataCode']
    dest_city = fare['arrivalAirport']['city']['name']

    fares = []
    for month in get_months_between(datetime_min, datetime_max):
        all_fares = get_cheapest_per_day(home_iata, dest_iata, month)
        fares += list(filter(lambda fare: fares_filter(
            fare=fare,
            datetime_min=datetime_min,
            datetime_max=datetime_max,
            price_max=price_max,
        ), all_fares))

    return [enrich_fare_info(fare, home_iata, home_city, dest_iata, dest_city) for fare in fares]

def find_return_trips(args):
    trips = []
    api_params = {
        "currency": config.CURRENCY,
        "departureAirportIataCodes": args.home_airports,
        "outboundDepartureDateFrom": args.date_min,
        "outboundDepartureDateTo": add_days_to_date(args.date_max, -1 * args.days_min),
        "priceValueTo": int(args.price_max - config.PRICE_LOWEST),
    }
    if args.dest_country:
        api_params["arrivalCountryCode"] = args.dest_country
    elif args.dest_airports:
        api_params["arrivalAirportIataCodes"] = args.dest_airports

    outFares = []
    for fare in get_cheapest_fares(api_params):
        outFares += find_alternative_fares(
            fare=fare,
            datetime_min=datetime.fromisoformat(args.date_min),
            datetime_max=datetime.fromisoformat(args.date_max) - timedelta(days=args.days_min),
            price_max=int(args.price_max - config.PRICE_LOWEST),
        )

    for outFare in outFares:
        datetime_min = (datetime.fromisoformat(outFare['arrivalDate']) + timedelta(days=args.days_min)).replace(hour=0, minute=0)
        datetime_max = min(
            datetime.fromisoformat(args.date_max),
            datetime.fromisoformat(outFare['arrivalDate']) + timedelta(days=args.days_max)
        ).replace(hour=23, minute=59)
        price_max = int(args.price_max - outFare['price']['value'])

        api_params = {
            "currency": config.CURRENCY,
            "departureAirportIataCode": outFare['arrivalAirport']['iataCode'],
            "arrivalAirportIataCodes": args.home_airports,
            "outboundDepartureDateFrom": datetime_min.strftime("%Y-%m-%d"),
            "outboundDepartureDateTo": datetime_max.strftime("%Y-%m-%d"),
            "priceValueTo": price_max
        }
        returnFares = []
        for fare in get_cheapest_fares(api_params):
            returnFares += find_alternative_fares(
                fare=fare,
                datetime_min=datetime_min,
                datetime_max=datetime_max,
                price_max=price_max,
            )

        for returnFare in returnFares:
            trips.append(create_trip(outFare, returnFare))

    trips.sort(key=lambda x: x['totalPrice'])
    return trips
