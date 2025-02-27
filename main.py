#!/usr/bin/env python
import json
import logging
import sys
from datetime import datetime
import api
from trips import search_multi_home_return_trips, search_single_home_return_trips
from config import parse_args

def main():
    args = parse_args()

    if args.days_min > args.days_max:
        sys.exit("days-min cannot be greater than days-max")
    if args.passengers < 1:
        sys.exit("number of passengers cannot be less than 1")
    if datetime.fromisoformat(args.date_min) < datetime.today():
        sys.exit("date-min cannot be earlier than today")
    if datetime.fromisoformat(args.date_max) < datetime.today():
        sys.exit("date-max cannot be earlier than today")

    if args.command == "search":
        if args.subcommand == "return":
            if len(args.home_airports) == 1:
                trips = search_single_home_return_trips(args)
            else:
                trips = search_multi_home_return_trips(args)
            print(json.dumps(trips, indent=2))
        if args.subcommand == "oneway":
            pass

    logging.info("Made %d requests to the API in total", api.request_count)

if __name__ == "__main__":
    main()
