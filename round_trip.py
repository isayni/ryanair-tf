#!/usr/bin/env python
import requests
import os
'''
Find cheapest round trip with Ryanair
'''

API_URL="https://services-api.ryanair.com/farfnd/v4/"

DISCORD      = os.getenv("DISCORD")          # discord webhook URL
CURRENCY     = os.getenv("CURRENCY")         # eg PLN
DATE_FROM    = os.getenv("DATE_FROM")        # eg 2024-06-01
DATE_TO      = os.getenv("DATE_TO")          # eg 2024-06-30
DAYS_MIN     = int(os.getenv("DAYS_MIN"))    # eg 3
DAYS_MAX     = int(os.getenv("DAYS_MAX"))    # eg 6
HOME_AIRPORT = os.getenv("HOME_AIRPORT")     # eg KRK
DEST_AIRPORT = os.getenv("DEST_AIRPORT")     # eg FCO
PASSENGERS   = int(os.getenv("PASSENGERS"))  # eg 3
PRICE_MAX    = float(os.getenv("PRICE_MAX")) # eg 600

def notify(message):
    if DISCORD:
        requests.post(DISCORD, json={"content": message})
    print(message)

params = {
    "currency": CURRENCY,
    "departureAirportIataCode": HOME_AIRPORT,
    "arrivalAirportIataCode": DEST_AIRPORT,
    "outboundDepartureDateFrom": DATE_FROM,
    "outboundDepartureDateTo": DATE_TO,
    "inboundDepartureDateFrom": DATE_FROM,
    "inboundDepartureDateTo": DATE_TO,
    "durationFrom": DAYS_MIN,
    "durationTo": DAYS_MAX,
    "adultPaxCount": PASSENGERS,
    "limit": "1",
}

trip = requests.get(API_URL + "roundTripFares", params=params).json()['fares'][0]

link = f"https://www.ryanair.com/pl/pl/trip/flights/select?adults={PASSENGERS}&dateOut={trip['outbound']['departureDate'].split('T')[0]}&dateIn={trip['inbound']['departureDate'].split('T')[0]}&isReturn=true&originIata={HOME_AIRPORT}&destinationIata={DEST_AIRPORT}"

message = f'''
# [trip found!]({link}) ({PASSENGERS} passengers)
### {HOME_AIRPORT} -> {DEST_AIRPORT}:
{trip['outbound']['departureDate'].split('T')[0]} at {trip['outbound']['departureDate'].split('T')[1]} - **{trip['outbound']['price']['value'] / PASSENGERS} {CURRENCY}**
### {DEST_AIRPORT} -> {HOME_AIRPORT}:
{trip['inbound']['departureDate'].split('T')[0]} at {trip['inbound']['departureDate'].split('T')[1]} - **{trip['inbound']['price']['value'] / PASSENGERS} {CURRENCY}**

Total price: **{trip['summary']['price']['value']} {CURRENCY}** (**{trip['summary']['price']['value'] / PASSENGERS}** per person)
'''

if trip['summary']['price']['value'] / PASSENGERS <= PRICE_MAX:
    notify(message)

