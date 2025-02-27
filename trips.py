from datetime import datetime, timedelta
from utils import get_months_between, add_days_to_date, enrich_flight_info, create_trip
from api import get_cheapest_flights, get_cheapest_per_day, get_round_trip_fares

def find_alternative_flights(flight, datetime_min, datetime_max, price_max):
    def flights_filter(flight, datetime_min, datetime_max, price_max):
        datetime_max.replace(hour=23, minute=59)

        if flight['price'] is None or flight['price']['value'] > price_max:
            return False

        datetime_flight = datetime.fromisoformat(flight['departureDate'])

        if datetime_flight < datetime_min or datetime_flight > datetime_max:
            return False

        return True

    home_iata = flight['departureAirport']['iataCode']
    home_city = flight['departureAirport']['city']['name']
    dest_iata = flight['arrivalAirport']['iataCode']
    dest_city = flight['arrivalAirport']['city']['name']

    flights = []
    for month in get_months_between(datetime_min, datetime_max):
        fares = get_cheapest_per_day(home_iata, dest_iata, month)
        all_flights = fares['outbound']['fares'] if 'outbound' in fares else []
        flights += list(filter(lambda flight: flights_filter(
            flight=flight,
            datetime_min=datetime_min,
            datetime_max=datetime_max,
            price_max=price_max,
        ), all_flights))

    return [enrich_flight_info(flight, home_iata, home_city, dest_iata, dest_city) for flight in flights]

def find_alternative_round_trips(fare, args):
    home_iata = fare['outbound']['departureAirport']['iataCode']
    home_city = fare['outbound']['departureAirport']['city']['name']
    dest_iata = fare['outbound']['arrivalAirport']['iataCode']
    dest_city = fare['outbound']['arrivalAirport']['city']['name']

    datetime_min = datetime.fromisoformat(args.date_min)
    datetime_max = datetime.fromisoformat(args.date_max)

    outbounds = []
    inbounds = []
    for month in get_months_between(datetime_min, datetime_max):
        fares = get_cheapest_per_day(home_iata, dest_iata, month)
        outbounds += fares['outbound']['fares']
        inbounds  += fares['inbound']['fares']

    trips = []
    for i, outbound in enumerate(outbounds):
        if outbound['unavailable']:
            continue
        date_out = datetime.fromisoformat(outbound['departureDate'])
        if date_out < datetime_min or date_out > datetime_max:
            continue
        if outbound['price']['value'] - args.price_lowest > args.price_max:
            continue

        for j in range(args.days_min, args.days_max + 1):
            inbound = inbounds[i + j]
            if inbound['unavailable']:
                continue
            date_in = datetime.fromisoformat(inbound['departureDate'])
            if date_in < datetime.fromisoformat(outbound['arrivalDate']) + timedelta(hours=args.hours_min):
                continue
            if inbound['price']['value'] + outbound['price']['value'] <= args.price_max:
                outbound = enrich_flight_info(outbound, home_iata, home_city, dest_iata, dest_city)
                inbound = enrich_flight_info(inbound, dest_iata, dest_city, home_iata, home_city)
                trips.append(create_trip(outbound, inbound))
    return trips

def search_single_home_return_trips(args):
    trips = []
    for fare in get_round_trip_fares(args):
        trips += find_alternative_round_trips(fare, args)

    trips.sort(key=lambda x: x['totalPrice'])
    return trips


def search_multi_home_return_trips(args):
    trips = []
    out_flights = []
    for flight in get_cheapest_flights(
        home_airports=args.home_airports,
        date_min=args.date_min,
        date_max=add_days_to_date(args.date_max, -1 * args.days_min),
        price_max=int(args.price_max - args.price_lowest),
        dest_country=args.dest_country,
        dest_airports=args.dest_airports
    ):
        out_flights += find_alternative_flights(
            flight=flight,
            datetime_min=datetime.fromisoformat(args.date_min),
            datetime_max=datetime.fromisoformat(args.date_max) - timedelta(days=args.days_min),
            price_max=int(args.price_max - args.price_lowest),
        )

    for out_flight in out_flights:
        if args.days_min == 0:
            datetime_min = datetime.fromisoformat(out_flight['arrivalDate']) + timedelta(hours=args.hours_min)
        else:
            datetime_min = (datetime.fromisoformat(out_flight['arrivalDate']) + timedelta(days=args.days_min)).replace(hour=0, minute=0)
        datetime_max = min(
            datetime.fromisoformat(args.date_max),
            datetime.fromisoformat(out_flight['arrivalDate']) + timedelta(days=args.days_max)
        ).replace(hour=23, minute=59)
        price_max = int(args.price_max - out_flight['price']['value'])

        return_flights = []
        for flight in get_cheapest_flights(
            home_airports=[out_flight['arrivalAirport']['iataCode']],
            date_min=datetime_min.strftime("%Y-%m-%d"),
            date_max=datetime_max.strftime("%Y-%m-%d"),
            price_max=price_max,
            dest_airports=args.home_airports
        ):
            return_flights += find_alternative_flights(
                flight=flight,
                datetime_min=datetime_min,
                datetime_max=datetime_max,
                price_max=price_max,
            )
        for return_flight in return_flights:
            trips.append(create_trip(out_flight, return_flight))

    trips.sort(key=lambda x: x['totalPrice'])
    return trips
