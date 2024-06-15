#!/usr/bin/env python
from myproxies import sendRequest
import os
import json
'''
Find cheapest round trips with Ryanair
'''

API_URL="https://services-api.ryanair.com/farfnd/v4/"

CURRENCY     = "PLN"
DATE_FROM    = "2024-07-13"
DATE_TO      = "2024-08-01"
DAYS_MIN     = 2
DAYS_MAX     = 4
HOME_AIRPORT = "KRK"
PASSENGERS   = 4
PRICE_MAX    = 500

params = {
    "currency": CURRENCY,
    "departureAirportIataCode": HOME_AIRPORT,
    "outboundDepartureDateFrom": DATE_FROM,
    "outboundDepartureDateTo": DATE_TO,
    "inboundDepartureDateFrom": DATE_FROM,
    "inboundDepartureDateTo": DATE_TO,
    "durationFrom": DAYS_MIN,
    "durationTo": DAYS_MAX,
    "adultPaxCount": PASSENGERS,
    "priceValueTo": PRICE_MAX * PASSENGERS,
}

response = sendRequest(API_URL + "roundTripFares", params=params)

fares = response.json()['fares']
trips = {}

for f in fares:
    trips[f['outbound']['arrivalAirport']['city']['name']] = {
        "price": f['summary']['price']['value'] / PASSENGERS,
        "outbound": f['outbound']['departureDate'],
        "inbound": f['inbound']['departureDate']
    }

print(json.dumps(trips, indent=2))

