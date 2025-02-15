from datetime import datetime, timedelta

def add_days_to_date(date, days):
    obj = datetime.fromisoformat(date)
    return (obj + timedelta(days=days)).strftime("%Y-%m-%d")

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

def enrich_fare_info(fare, home_iata, home_city, dest_iata, dest_city):
    fare['departureAirport'] = {
        'iataCode': home_iata,
        'city': {
            'name': home_city
        }
    }
    fare['arrivalAirport'] = {
        'iataCode': dest_iata,
        'city': {
            'name': dest_city
        }
    }
    return fare

def create_trip(outFare, returnFare):
    return {
        'outbound': {
            'home': f'{outFare["departureAirport"]["city"]["name"]}/{outFare["departureAirport"]["iataCode"]}',
            'destination': f'{outFare["arrivalAirport"]["city"]["name"]}/{outFare["arrivalAirport"]["iataCode"]}',
            'takeoff': outFare["departureDate"],
            'price': outFare["price"]["value"]
        },
        'inbound': {
            'home': f'{returnFare["departureAirport"]["city"]["name"]}/{returnFare["departureAirport"]["iataCode"]}',
            'destination': f'{returnFare["arrivalAirport"]["city"]["name"]}/{returnFare["arrivalAirport"]["iataCode"]}',
            'takeoff': returnFare["departureDate"],
            'price': returnFare["price"]["value"]
        },
        'totalPrice': outFare["price"]["value"] + returnFare["price"]["value"]
    }
