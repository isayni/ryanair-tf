#!/usr/bin/env python
from datetime import datetime, timedelta
import os
import json
import requests
'''
find ryanair round trips allowing multiple options for the "home" airport
'''

API_URL   = "https://services-api.ryanair.com/farfnd/v4/"
MYPROXIES = False

CURRENCY      = os.getenv("CURRENCY")                 # eg PLN
DATE_FROM     = os.getenv("DATE_FROM")                # eg 2024-06-01
DATE_TO       = os.getenv("DATE_TO")                  # eg 2024-06-30
DAYS_MIN      = int(os.getenv("DAYS_MIN"))            # eg 3
DAYS_MAX      = int(os.getenv("DAYS_MAX"))            # eg 6
HOME_AIRPORTS = os.getenv("HOME_AIRPORTS").split(',') # eg KRK,KTW
DEST_AIRPORTS = os.getenv("DEST_AIRPORTS").split(',') # eg FCO,CPH
PRICE_MAX     = float(os.getenv("PRICE_MAX"))         # eg 600
PASSENGERS    = int(os.getenv("PASSENGERS"))          # eg 3

def findFares(params):
    response = requests.get(API_URL + "oneWayFares", params=params).json()
    return response['fares'] if response['fares'] else []

def getDate(d, days):
    obj = datetime.strptime(d, "%Y-%m-%dT%H:%M:%S")
    return (obj + timedelta(days=days)).strftime("%Y-%m-%d")

def createTrip(outFare, returnFare):
    trip = {'outbound': {}, 'inbound': {}}
    trip['outbound']['home'] = outFare['outbound']['departureAirport']['city']['name']
    trip['outbound']['destination'] = outFare['outbound']['arrivalAirport']['city']['name']
    trip['outbound']['takeoff'] = outFare['outbound']['departureDate']
    trip['outbound']['price'] = outFare['outbound']['price']['value']
    trip['inbound']['home'] = returnFare['outbound']['departureAirport']['city']['name']
    trip['inbound']['destination'] = returnFare['outbound']['arrivalAirport']['city']['name']
    trip['inbound']['takeoff'] = returnFare['outbound']['departureDate']
    trip['inbound']['price'] = returnFare['outbound']['price']['value']
    trip['totalPrice'] = outFare['outbound']['price']['value'] + returnFare['outbound']['price']['value']
    return trip

if __name__ == "__main__":
    outFares = []
    trips = []
    for home in HOME_AIRPORTS:
        params = {
            "currency": CURRENCY,
            "departureAirportIataCode": home,
            "outboundDepartureDateFrom": DATE_FROM,
            "outboundDepartureDateTo": DATE_TO,
            "priceValueTo": PRICE_MAX - 50,
        }
        outFares += [fare for fare in findFares(params) if fare['outbound']['arrivalAirport']['iataCode'] in DEST_AIRPORTS]

    for outFare in outFares:
        params = {
            "currency": CURRENCY,
            "departureAirportIataCode": outFare['outbound']['arrivalAirport']['iataCode'],
            "outboundDepartureDateFrom": getDate(outFare['outbound']['arrivalDate'], DAYS_MIN),
            "outboundDepartureDateTo": getDate(outFare['outbound']['arrivalDate'], DAYS_MAX),
            "priceValueTo": (PRICE_MAX - outFare['outbound']['price']['value']),
        }
        returnFares = [fare for fare in findFares(params) if fare['outbound']['arrivalAirport']['iataCode'] in HOME_AIRPORTS]
        for returnFare in returnFares:
            trips.append(createTrip(outFare, returnFare))

    trips.sort(key=lambda x: x['totalPrice'])
    print(json.dumps(trips, indent=2))
