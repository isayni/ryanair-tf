#!/usr/bin/env python
import json
import logging
import api
from trips import search_multi_home_return_trips, search_single_home_return_trips, search_one_way_trips
from config import parse_args

def main():
    args = parse_args()

    if args.command == "search":
        trips = []
        if args.subcommand == "return":
            if len(args.home_airports) == 1:
                trips = search_single_home_return_trips(args)
            else:
                trips = search_multi_home_return_trips(args)
        if args.subcommand == "oneway":
            trips = search_one_way_trips(args)

        print(json.dumps(trips, indent=2))

    logging.info("Made %d requests to the API in total", api.request_count)

if __name__ == "__main__":
    main()
