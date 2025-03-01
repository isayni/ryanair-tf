from datetime import datetime, timedelta

def get_months_between(datetime_min, datetime_max):
    current = datetime_min.replace(day=1)
    end = datetime_max

    first_days = []

    while current <= end:
        first_days.append(current.strftime("%Y-%m-%d"))

        next_month = current.month + 1 if current.month < 12 else 1
        next_year = current.year if current.month < 12 else current.year + 1
        current = current.replace(year=next_year, month=next_month, day=1)

    return first_days

def enrich_flight_info(flight, home_iata, home_city, dest_iata, dest_city):
    flight['departureAirport'] = {
        'iataCode': home_iata,
        'city': {
            'name': home_city
        }
    }
    flight['arrivalAirport'] = {
        'iataCode': dest_iata,
        'city': {
            'name': dest_city
        }
    }
    return flight

def create_trip(out_fare, return_fare=None):
    trip = {
        'outbound': {
            'home': f'{out_fare["departureAirport"]["city"]["name"]}/{out_fare["departureAirport"]["iataCode"]}',
            'destination': f'{out_fare["arrivalAirport"]["city"]["name"]}/{out_fare["arrivalAirport"]["iataCode"]}',
            'departure': out_fare["departureDate"],
            'arrival': out_fare["arrivalDate"],
            'price': out_fare["price"]["value"]
        }
    }
    if return_fare:
        trip['inbound'] = {
            'home': f'{return_fare["departureAirport"]["city"]["name"]}/{return_fare["departureAirport"]["iataCode"]}',
            'destination': f'{return_fare["arrivalAirport"]["city"]["name"]}/{return_fare["arrivalAirport"]["iataCode"]}',
            'departure': return_fare["departureDate"],
            'arrival': return_fare["arrivalDate"],
            'price': return_fare["price"]["value"]
        }
        trip['totalPrice'] = out_fare["price"]["value"] + return_fare["price"]["value"]
    else:
        trip['totalPrice'] = out_fare["price"]["value"]
    return trip
