import argparse
from datetime import datetime, timedelta
import logging

API_URL  = "https://services-api.ryanair.com/farfnd/v4/"
CURRENCY = "EUR"

def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", help="command to use", required=True)
    search_parser = subparsers.add_parser("search")
    search_subparsers = search_parser.add_subparsers(dest="subcommand", help="what to search for")
    search_oneway_parser = search_subparsers.add_parser("oneway")
    search_return_parser = search_subparsers.add_parser("return")

    parser.add_argument("--debug", action="store_true", default=False, help="print debug information")
    parser.add_argument("--currency", default="EUR", help="code of currency to use")

    def add_common_arguments_search(parser):
        parser.add_argument("--date-min", default=datetime.today().strftime("%Y-%m-%d"), help="start of the calendar window to search")
        parser.add_argument("--date-max", default=(datetime.today() + timedelta(days=30)).strftime("%Y-%m-%d"), help="end of the calendar window to search")
        parser.add_argument("--home-airports", nargs="+", required=True, help="list of airports' iata codes to fly from and return to")
        parser.add_argument("--price-max", type=float, required=True, help="the maximum cost in the specified currency of the whole trip")
        # parser.add_argument("--passengers", type=int, default=1, help="number of passengers")
        dest_group = parser.add_mutually_exclusive_group(required=False)
        dest_group.add_argument("--dest-airports", nargs="+", help="list of destination airports' iata codes")
        dest_group.add_argument("--dest-country", help="code of destination country")

    add_common_arguments_search(search_oneway_parser)
    add_common_arguments_search(search_return_parser)

    search_return_parser.add_argument("--price-lowest", type=float, default=0, help="the lowest price of a flight in the specified currency that you expect to find (use for better optimization)")
    search_return_parser.add_argument("--days-min", default=1, type=int, help="minimum number of days for the whole trip")
    search_return_parser.add_argument("--days-max", default=7, type=int, help="maximum number of days for the whole trip")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.ERROR
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] [%(module)s.%(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    global CURRENCY

    CURRENCY     = args.currency

    return args
