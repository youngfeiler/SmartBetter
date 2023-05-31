import time

import historical_odds_getter
import current_odds_getter
from scrapers import draftkings_scraper, barstool_scraper, betonlineag_scraper
import bet_processor
from bots import barstool, betonlineag, draftkings
from scripts import notification
from scripts.bots import mybookieag



params = {
    "DAYS_TO_RUN": 7,
    "HOURS_TO_CHECK": [21, 22, 23, 24, 1, 2, 3, 4, 5, 6, 7],
    "BOOKMAKERS_LIST": [
        "barstool", "betfair", "betmgm", "betonlineag", "betrivers", "bovada", "circasports", "draftkings", "fanduel",
        "mybookieag"
        "foxbet", "gtbets", "pinnacle", "pointsbetus", "sugarhouse", "twinspires", "unibet_us", "williamhill_us",
        "wynnbet", "superbook", "lowvig", "betus"
    ],
    'BOOKMAKERS_TO_SCAN': ["draftkings"],
    'BOOKMAKERS_TO_SCAN_AS_LIST': ["draftkings"],
    "SCORES_PATHNAME": f".data/scores.xlsx",
    "ODDS_PATHNAME": f".data/historical_odds.csv",
    "DAYS": 7,
    "EV": 10,
    "STAKE": 1,
    "DRIVERS": {},
    "SCRAPERS": {},
    "MAX ODDS": 1000,
    "NBA TEAMS": [],
    "ACCURATE_BOOKMAKER": ''
}


def initialize_scrapers(params) -> dict:
    #params["SCRAPERS"]['draftkings'] = draftkings_scraper.open_browser()
    #print("DK scraper initialized")
    params["SCRAPERS"]['barstool'] = barstool_scraper.open_browser()
    print("Barstool scraper initialized")

    #params["SCRAPERS"]['betonlineag'] = betonlineag_scraper.open_browser()
    #print("Betonlineag scraper initialized")

    #params["SCRAPERS"]['mybookieag'] = params['DRIVERS']['mybookieag']
    #print("Mybookie scraper initialized")

    print("All scrapers initialized")

    return params

def restart_scrapers(params) -> dict:
    #params["SCRAPERS"]['draftkings'].quit()
    params["SCRAPERS"]['barstool'].quit()
    #params["SCRAPERS"]['betonlineag'].quit()
    #params['SCRAPERS']['mybookieag'].quit()

    #params["SCRAPERS"]['draftkings'] = draftkings_scraper.open_browser()
    params["SCRAPERS"]['barstool'] = barstool_scraper.open_browser()
    #params["SCRAPERS"]['betonlineag'] = betonlineag_scraper.open_browser()
    #params['SCRAPERS']['mybookieag'] = params['DRIVERS']['mybookieag']

    print("Scrapers re-initialized")
    return params


def initialize_drivers(params) -> dict:
    params['DRIVERS']['barstool'] = barstool.open_browser()
    #params['DRIVERS']['betonlineag'] = betonlineag.open_browser()
    #params['DRIVERS']['draftkings'] = draftkings.open_browser()
    #params['DRIVERS']['mybookieag'] = mybookieag.open_browser()
    print("Bots initialized")
    return params

def restart_drivers(params)->dict:
    #params["DRIVERS"]['draftkings'].quit()
    params["DRIVERS"]['barstool'].quit()
    #params['DRIVERS']['betonlineag'].quit()
   # params['DRIVERS']['mybookieag'].quit()

    #params["DRIVERS"]['draftkings'] = draftkings.open_browser()
    params["DRIVERS"]['barstool'] = barstool.open_browser()
    #params['DRIVERS']['betonlineag'] = betonlineag.open_browser()
    #params['DRIVERS']['mybookieag'] = mybookieag.open_browser()

    print("Bots re-initialized")
    return params

def initialize_accurate_bookmaker(params) -> dict:
    # Returns the most accurate bookmaker
    #accurate_bookmaker = historical_odds_getter.run()
    accurate_bookmaker = "draftkings"

    params["ACCURATE_BOOKMAKER"] = [accurate_bookmaker]

    print(params["ACCURATE_BOOKMAKER"])

    return params


if __name__ == '__main__':

    params = initialize_accurate_bookmaker(params)

    params = initialize_drivers(params)

    params = initialize_scrapers(params)

    check_list = []

    count = 0

    start_time = time.time()
    start_time2 = time.time()

    while True:
        try:
            start = time.time()

            data = current_odds_getter.get_data(bookmakers='draftkings')

            params = current_odds_getter.make_list_of_live_games(data=data, params=params)

            dicts = [
                #betonlineag_scraper.store_in_dict(params["SCRAPERS"]['betonlineag'], params),
                #draftkings_scraper.store_in_dict(params["SCRAPERS"]['draftkings'], params),
                barstool_scraper.store_in_dict(params["SCRAPERS"]['barstool'], params),
                #mybookieag.store_in_dict(params['SCRAPERS']['mybookieag'],params)
            ]

            names = [
                #"BetOnlineag",
                #"DraftKings",
                "Barstool"
                #"MyBookie"
            ]

            compiled = {}

            for team in set(team for d in dicts for team in d.keys()):
                compiled[team] = {name: d.get(team, 0) for name, d in zip(names, dicts)}

            data = current_odds_getter.get_data(bookmakers='draftkings')

            if bool(compiled) > 0:
                ev_dict, odds_dict = current_odds_getter.run(data=data, scraped_odds_dict=compiled, params=params)
                bet_processor.process(ev_dict=ev_dict, odds_dict=odds_dict, params=params, check_list=check_list)

            print(F'Bet List: {check_list}')

            end = time.time()

            print(f"Total Time to Run: {round((end - start), 1)}s")

            #time.sleep(2)

            if time.time() - start_time > 300:

                start_time = time.time()

            # check if 10 minutes have passed
            elif time.time() - start_time2 > 600:

                params = restart_drivers(params=params)

                params = restart_scrapers(params=params)

                # clear the list
                check_list = []

                start_time2 = time.time()

                count += 1

                print(f"Round{count}")

        except:
            print("Couldn't do this round for some reason")
