#!/usr/bin/env python
import json
import logging
import api
from config import parse_args

def main():
    args = parse_args()

    if args.command == "search":
        if args.subcommand == "return":
            trips = api.find_return_trips(args)
            print(json.dumps(trips, indent=2))
        if args.subcommand == "oneway":
            pass

    logging.info("Made %d requests to the API in total", api.request_count)

if __name__ == "__main__":
    main()
