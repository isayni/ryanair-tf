#!/usr/bin/env python
from datetime import datetime, timedelta
from functools import wraps
import argparse
import logging
import os
import json
import requests
'''
find ryanair round trips allowing multiple options for the "home" airport
'''

API_URL      = "https://services-api.ryanair.com/farfnd/v4/"
ARGS = None

def add_common_arguments_search(parser):
    parser.add_argument("--date-min", default=datetime.today().strftime("%Y-%m-%d"), help="start of the calendar window to search")
    parser.add_argument("--date-max", default=(datetime.today() + timedelta(days=30)).strftime("%Y-%m-%d"), help="end of the calendar window to search")
    parser.add_argument("--home-airports", nargs="+", required=True, help="list of airports' iata codes to fly from and return to")
    parser.add_argument("--price-max", type=float, required=True, help="the maximum cost in the specified currency of the whole trip")
    parser.add_argument("--currency", default="EUR", help="code of currency to use")
    parser.add_argument("--passengers", type=int, default=1, help="number of passengers")
    dest_group = parser.add_mutually_exclusive_group(required=False)
    dest_group.add_argument("--dest-airports", nargs="+", help="list of destination airports' iata codes")
    dest_group.add_argument("--dest-country", help="code of destination country")

def setup_parser():
    global ARGS
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", help="command to use", required=True)
    search_parser = subparsers.add_parser("search")
    search_subparsers = search_parser.add_subparsers(dest="subcommand", help="what to search for")
    search_oneway_parser = search_subparsers.add_parser("oneway")
    search_return_parser = search_subparsers.add_parser("return")

    parser.add_argument("--debug", action="store_true", default=False, help="print debug information")

    add_common_arguments_search(search_oneway_parser)
    add_common_arguments_search(search_return_parser)

    search_return_parser.add_argument("--lowest-price", type=float, default=0, help="the lowest price of a flight in the specified currency that you expect to find (use for better optimization)")
    search_return_parser.add_argument("--days-min", default=1, type=int, help="minimum number of days for the whole trip")
    search_return_parser.add_argument("--days-max", default=7, type=int, help="maximum number of days for the whole trip")

    ARGS = parser.parse_args()

    log_level = logging.DEBUG if ARGS.debug else logging.ERROR
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] [%(module)s.%(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

request_count = 0
def count_requests(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global request_count
        request_count += 1
        return func(*args, **kwargs)
    return wrapper

requests.get = count_requests(requests.get)

def add_days_to_date(d, days):
    obj = datetime.fromisoformat(d)
    return (obj + timedelta(days=days)).strftime("%Y-%m-%d")

def get_months_between(dateMin, dateMax):
    current = datetime.strptime(dateMin, "%Y-%m-%d").replace(day=1)
    end = datetime.strptime(dateMax, "%Y-%m-%d")

    first_days = []

    while current <= end:
        first_days.append(current.strftime("%Y-%m-%d"))

        next_month = current.month + 1 if current.month < 12 else 1
        next_year = current.year if current.month < 12 else current.year + 1
        current = current.replace(year=next_year, month=next_month, day=1)

    return first_days

flight_to_fare = lambda flight, homeIata, homeCity, destIata, destCity: {
    'outbound': {
        'departureAirport': {
            'iataCode': homeIata,
            'city': {
                'name': homeCity
            }
        },
        'arrivalAirport': {
            'iataCode': destIata,
            'city': {
                'name': destCity
            }
        },
        'departureDate': flight["departureDate"],
        'arrivalDate': flight["arrivalDate"],
        'price': {
            'value': flight["price"]["value"]
        }
    }
}

create_trip = lambda outFare, returnFare: {
    'outbound': {
        'home': f'{outFare["outbound"]["departureAirport"]["city"]["name"]}/{outFare["outbound"]["departureAirport"]["iataCode"]}',
        'destination': f'{outFare["outbound"]["arrivalAirport"]["city"]["name"]}/{outFare["outbound"]["arrivalAirport"]["iataCode"]}',
        'takeoff': outFare["outbound"]["departureDate"],
        'price': outFare["outbound"]["price"]["value"]
    },
    'inbound': {
        'home': f'{returnFare["outbound"]["departureAirport"]["city"]["name"]}/{returnFare["outbound"]["departureAirport"]["iataCode"]}',
        'destination': f'{returnFare["outbound"]["arrivalAirport"]["city"]["name"]}/{returnFare["outbound"]["arrivalAirport"]["iataCode"]}',
        'takeoff': returnFare["outbound"]["departureDate"],
        'price': returnFare["outbound"]["price"]["value"]
    },
    'totalPrice': outFare["outbound"]["price"]["value"] + returnFare["outbound"]["price"]["value"]
}

def find_cheapest_fares(params):
    data = requests.get(API_URL + "oneWayFares", params=params).json()
    return data['fares'] if 'fares' in data else []

def alternative_flights_filter(flight, minDate, maxDate, maxPrice):
    if flight['price'] is None or flight['price']['value'] > maxPrice:
        return False

    minDatetime = datetime.strptime(minDate, "%Y-%m-%d")
    maxDatetime = datetime.strptime(maxDate, "%Y-%m-%d")
    flightDatetime = datetime.fromisoformat(flight['departureDate'])

    if flightDatetime < minDatetime:
        return False
    if flightDatetime - timedelta(days=ARGS.days_min) > maxDatetime:
        return False

    return True

def find_alternative_fares(fare, minDate, maxDate, maxPrice):
    home     = fare['outbound']['departureAirport']['iataCode']
    homeCity = fare['outbound']['departureAirport']['city']['name']
    dest     = fare['outbound']['arrivalAirport']['iataCode']
    destCity = fare['outbound']['arrivalAirport']['city']['name']
    flights = []

    for month in get_months_between(minDate, maxDate):
        params = {
            "currency": ARGS.currency,
            "outboundMonthOfDate": month,
        }

        data = requests.get(API_URL + f"oneWayFares/{home}/{dest}/cheapestPerDay", params=params).json()
        flights += list(filter(lambda f: alternative_flights_filter(f, minDate, maxDate, maxPrice), data['outbound']['fares']))

    return [flight_to_fare(flight, home, homeCity, dest, destCity) for flight in flights]

def find_return_trips():
    trips = []
    params = {
        "currency": ARGS.currency,
        "departureAirportIataCodes": ARGS.home_airports,
        "outboundDepartureDateFrom": ARGS.date_min,
        "outboundDepartureDateTo": ARGS.date_max,
        "priceValueTo": int(ARGS.price_max - ARGS.lowest_price),
    }
    if ARGS.dest_country: # destination country is specified
        params["arrivalCountryCode"] = ARGS.dest_country
    elif "" not in ARGS.dest_airports: # destination airport(s) specified
        params["arrivalAirportIataCodes"] = ARGS.dest_airports

    outFares = []
    for fare in find_cheapest_fares(params):
        outFares += find_alternative_fares(fare, ARGS.date_min, ARGS.date_max, int(ARGS.price_max - ARGS.lowest_price))

    for outFare in outFares:
        maxPrice = int(ARGS.price_max - outFare['outbound']['price']['value'])
        minDate = add_days_to_date(outFare['outbound']['arrivalDate'], ARGS.days_min)
        maxDate = add_days_to_date(outFare['outbound']['arrivalDate'], ARGS.days_max)
        params = {
            "currency": ARGS.currency,
            "departureAirportIataCode": outFare['outbound']['arrivalAirport']['iataCode'],
            "arrivalAirportIataCodes": ARGS.home_airports,
            "outboundDepartureDateFrom": minDate,
            "outboundDepartureDateTo": maxDate,
            "priceValueTo": maxPrice
        }
        returnFares = []
        for fare in find_cheapest_fares(params):
            returnFares += find_alternative_fares(fare, minDate, maxDate, maxPrice)

        for returnFare in returnFares:
            trips.append(create_trip(outFare, returnFare))

    trips.sort(key=lambda x: x['totalPrice'])
    return trips

if __name__ == "__main__":
    setup_parser()
    if ARGS.command == "search":
        if ARGS.subcommand == "return":
            trips = find_return_trips()

            print(json.dumps(trips, indent=2))
            logging.info(f"Made {request_count} requests to the API in total")

