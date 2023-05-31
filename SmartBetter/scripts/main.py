import time
import os

# import barstool
# import betonlineag
# import current_odds_getter
# import fanduel
# import historical_odds_getter
# import machine_learning_model
# import mybookieag
# import betonlineag
# import draftkings
from scripts import historical_odds_getter, barstool, draftkings, current_odds_getter, betonlineag

params = {
    "DAYS_TO_RUN": 7,
    "HOURS_TO_CHECK": [21, 22, 23, 24, 1, 2, 3, 4, 5, 6, 7],
    "BOOKMAKERS_LIST": [
        "barstool", "betfair", "betmgm", "betonlineag", "betrivers", "bovada", "circasports", "draftkings", "fanduel",
        "mybookieag"
        "foxbet", "gtbets", "pinnacle", "pointsbetus", "sugarhouse", "twinspires", "unibet_us", "williamhill_us",
        "wynnbet", "superbook", "lowvig", "betus"
    ],
    'BOOKMAKERS_TO_SCAN': ["betmgm,draftkings,barstool,betonlineag"],
    'BOOKMAKERS_TO_SCAN_AS_LIST': ["betmgm","draftkings", "barstool", "betonlineag"],
    "SCORES_PATHNAME": f".data/scores.xlsx",
    "ODDS_PATHNAME": f".data/historical_odds.csv",
    "DAYS": 7,
    "EV": 10,
    "STAKE": 1,
    "DRIVERS": {},
    "MAX ODDS": 1000
}

def initialize_browsers(restart):
    if restart:
        params['DRIVERS']['barstool'].quit()
        params['DRIVERS']['draftkings'].quit()
        params['DRIVERS']['betonlineag'].quit()

    params['DRIVERS']['barstool'] = barstool.open_browser()
    params['DRIVERS']['draftkings'] = draftkings.open_browser()
    params['DRIVERS']['betonlineag'] = betonlineag.open_browser()


def initialize_accurate_bookmaker():
    accurate_bookmaker = historical_odds_getter.run()

    return accurate_bookmaker


def run(accurate_bookmaker, check_list):
    # Check the market for the current odds given the most accurate bookmaker and the books we can use
    test = current_odds_getter.run(params['BOOKMAKERS_TO_SCAN'][0], accurate_bookmaker,
                                   params['BOOKMAKERS_TO_SCAN_AS_LIST'], params, check_list)


if __name__ == '__main__':
    # Returns the most accurate bookmaker
    accurate_bookmaker = initialize_accurate_bookmaker()

    if accurate_bookmaker== "williamhill":
        accurate_bookmaker = "williamhill_us"

    print(accurate_bookmaker)

    initialize_browsers(False)

    # Creates the regresion that determines our confidence level and some more info about the bet
    #model = machine_learning_model.run()

    running = True

    start_time = time.time()
    start_time2 = time.time()
    start_time3 = time.time()

    check_list = []

    count = 0

    # Every 5 seconds, run the entire function
    while running:

        run(accurate_bookmaker, check_list)

        time.sleep(5)

        print(check_list)

        # Check if 5 minutes have passed
        if time.time() - start_time > 300:
            start_time = time.time()

            barstool.refresh(params['DRIVERS']['barstool'])

        # check if 10 minutes have passed
        elif time.time() - start_time2 > 600:
            # clear the list
            check_list = []
            # start a new timer
            start_time2 = time.time()
            # change the round count
            count += 1
            # print the round count
            print(f"Round{count}")

        # check if 20 minutes have passed
        elif time.time() - start_time3 > 1200:
            # close the bots and re-login to avoid logout-errors
            initialize_browsers(True)

            # start a new timer
            start_time3 = time.time()

            # print
            print("Browsers restarted successfuly")
