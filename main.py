#!/usr/bin/env python
import requests
import os

API_URL="https://services-api.ryanair.com/farfnd/v4/"

DISCORD      = os.environ.get("DISCORD")
CURRENCY     = os.environ.get("CURRENCY")
DATE_FROM    = os.environ.get("DATE_FROM")
DATE_TO      = os.environ.get("DATE_TO")
DAYS_MIN     = int(os.environ.get("DAYS_MIN"))
DAYS_MAX     = int(os.environ.get("DAYS_MAX"))
HOME_AIRPORT = os.environ.get("HOME_AIRPORT")
DEST_AIRPORT = os.environ.get("DEST_AIRPORT")
PASSENGERS   = int(os.environ.get("PASSENGERS"))
PRICE_MAX    = float(os.environ.get("PRICE_MAX"))

def notify(message):
    requests.post(DISCORD, json={"content": message})

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

print(message)

if trip['summary']['price']['value'] / PASSENGERS <= PRICE_MAX:
    notify(message)

