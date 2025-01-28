#!/usr/bin/env python
import myproxies
import os
import json
'''
Find cheapest round trips with Ryanair
'''

API_URL="https://services-api.ryanair.com/farfnd/v4/"

CURRENCY     = "PLN"
DATE_FROM    = "2025-02-02"
DATE_TO      = "2025-02-28"
DAYS_MIN     = 1
DAYS_MAX     = 3
HOME_AIRPORT = "KRK"
PASSENGERS   = 1
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

response = myproxies.get(API_URL + "roundTripFares", params=params)

fares = response.json()['fares']
trips = {}

for f in fares:
    trips[f['outbound']['arrivalAirport']['city']['name']] = {
        "price": f['summary']['price']['value'] / PASSENGERS,
        "outbound": f['outbound']['departureDate'],
        "inbound": f['inbound']['departureDate']
    }

print(json.dumps(trips, indent=2))

