#!/usr/bin/env python
from datetime import datetime, timedelta
from functools import wraps
import os
import json
import requests
'''
find ryanair round trips allowing multiple options for the "home" airport
'''

API_URL      = "https://services-api.ryanair.com/farfnd/v4/"
LOWEST_PRICE = 50

CURRENCY      = os.getenv("CURRENCY", "EUR")              # eg EUR
DATE_MIN      = os.getenv("DATE_MIN")                     # eg 2024-06-01
DATE_MAX      = os.getenv("DATE_MAX")                     # eg 2024-06-30
DAYS_MIN      = int(os.getenv("DAYS_MIN"))                # eg 3
DAYS_MAX      = int(os.getenv("DAYS_MAX"))                # eg 6
HOME_AIRPORTS = os.getenv("HOME_AIRPORTS").split(',')     # eg KRK,KTW
DEST_AIRPORTS = os.getenv("DEST_AIRPORTS", "").split(',') # eg FCO,CPH
PRICE_MAX     = float(os.getenv("PRICE_MAX"))             # eg 600
PASSENGERS    = int(os.getenv("PASSENGERS", 1))           # eg 3

request_count = 0
def count_requests(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global request_count
        request_count += 1
        return func(*args, **kwargs)
    return wrapper

requests.get = count_requests(requests.get)

def addDaysToDate(d, days):
    obj = datetime.fromisoformat(d)
    return (obj + timedelta(days=days)).strftime("%Y-%m-%d")

def findCheapestFares(params):
    data = requests.get(API_URL + "oneWayFares", params=params).json()
    return data['fares'] if 'fares' in data else []

def getMonthsBetween(dateMin, dateMax):
    current = datetime.strptime(dateMin, "%Y-%m-%d").replace(day=1)
    end = datetime.strptime(dateMax, "%Y-%m-%d")

    first_days = []

    while current <= end:
        first_days.append(current.strftime("%Y-%m-%d"))

        next_month = current.month + 1 if current.month < 12 else 1
        next_year = current.year if current.month < 12 else current.year + 1
        current = current.replace(year=next_year, month=next_month, day=1)

    return first_days

flightToFare = lambda flight, homeIata, homeCity, destIata, destCity: {
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

createTrip = lambda outFare, returnFare: {
    'outbound': {
        'home': outFare["outbound"]["departureAirport"]["city"]["name"],
        'destination': outFare["outbound"]["arrivalAirport"]["city"]["name"],
        'takeoff': outFare["outbound"]["departureDate"],
        'price': outFare["outbound"]["price"]["value"]
    },
    'inbound': {
        'home': returnFare["outbound"]["departureAirport"]["city"]["name"],
        'destination': returnFare["outbound"]["arrivalAirport"]["city"]["name"],
        'takeoff': returnFare["outbound"]["departureDate"],
        'price': returnFare["outbound"]["price"]["value"]
    },
    'totalPrice': outFare["outbound"]["price"]["value"] + returnFare["outbound"]["price"]["value"]
}

def alternativeFlightsFilter(flight, maxPrice):
    if flight['price'] is None:
        return False
    if flight['price']['value'] > maxPrice:
        return False

    minDatetime = datetime.strptime(DATE_MIN, "%Y-%m-%d")
    maxDatetime = datetime.strptime(DATE_MAX, "%Y-%m-%d")
    flightDatetime = datetime.fromisoformat(flight['departureDate'])
    if flightDatetime < minDatetime:
        return False
    if flightDatetime - timedelta(days=DAYS_MIN) > maxDatetime:
        return False

    return True

def findAlternativeFares(fare, maxPrice):
    home     = fare['outbound']['departureAirport']['iataCode']
    homeCity = fare['outbound']['departureAirport']['city']['name']
    dest     = fare['outbound']['arrivalAirport']['iataCode']
    destCity = fare['outbound']['arrivalAirport']['city']['name']
    flights = []

    for month in getMonthsBetween(DATE_MIN, DATE_MAX):
        params = {
            "currency": CURRENCY,
            "outboundMonthOfDate": month,
        }

        data = requests.get(API_URL + f"oneWayFares/{home}/{dest}/cheapestPerDay", params=params).json()
        flights += list(filter(lambda f: alternativeFlightsFilter(f, maxPrice), data['outbound']['fares']))

    return [flightToFare(flight, home, homeCity, dest, destCity) for flight in flights]

if __name__ == "__main__":
    trips = []
    params = {
        "currency": CURRENCY,
        "departureAirportIataCodes": HOME_AIRPORTS,
        "outboundDepartureDateFrom": DATE_MIN,
        "outboundDepartureDateTo": DATE_MAX,
        "priceValueTo": PRICE_MAX - LOWEST_PRICE,
    }
    if "" not in DEST_AIRPORTS:
        params["arrivalAirportIataCodes"] = DEST_AIRPORTS

    outFares = []
    for fare in findCheapestFares(params):
        outFares += findAlternativeFares(fare, PRICE_MAX - LOWEST_PRICE)

    for outFare in outFares:
        params = {
            "currency": CURRENCY,
            "departureAirportIataCode": outFare['outbound']['arrivalAirport']['iataCode'],
            "arrivalAirportIataCodes": HOME_AIRPORTS,
            "outboundDepartureDateFrom": addDaysToDate(outFare['outbound']['arrivalDate'], DAYS_MIN),
            "outboundDepartureDateTo": addDaysToDate(outFare['outbound']['arrivalDate'], DAYS_MAX),
            "priceValueTo": (PRICE_MAX - outFare['outbound']['price']['value']),
        }
        returnFares = []
        for fare in findCheapestFares(params):
            returnFares += findAlternativeFares(fare, PRICE_MAX - fare['outbound']['price']['value'])

        for returnFare in returnFares:
            trips.append(createTrip(outFare, returnFare))

    trips.sort(key=lambda x: x['totalPrice'])

    print(json.dumps(trips, indent=2))
    print(f"Made {request_count} requests to the API.")


