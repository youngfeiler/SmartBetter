import barstool, draftkings, current_odds_getter, betonlineag, place_bets, time, pickle, os

# TODO: CAP THE MAX LENGTH AT LIKE 5

params = {
    "BOOKMAKERS_DATA_LIST": [
        "barstool", "betmgm", "betonlineag", "betrivers", "bovada", "draftkings", "fanduel",
        "foxbet", "gtbets", "pinnacle", "pointsbetus", "sugarhouse", "twinspires", "unibet_us", "williamhill_us"
    ],
    'BOOKMAKERS_DATA_STRING': 'barstool,betmgm,betonlineag,betrivers,bovada,draftkings,fanduel,foxbet,gtbets,pinnacle,pointsbetus,sugarhouse,twinspires,unibet_us,williamhill_us',
    'BOOKMAKERS_TO_BET_WITH_STRING': "draftkings,barstool,betonlineag",
    'BOOKMAKERS_TO_BET_WITH_LIST': ["draftkings", "barstool", "betonlineag"],
    "DRIVERS": {},
    "MAX ODDS": 3,
    "MIN EV": 10,
    "STAKE": 1,
    "ANNUAL_MEAN_DECIMAL_ODDS": 2.503938607779538,
    "ANNUAL_STD_DECIMAL_ODDS": 3.0261868061051818,
    "ABS MINUTES SINCE GAME START": 120,
    "ODDS DICT": {}

}



def initialize(params: dict):

    def initialize_browsers(params: dict) -> dict:
        params['DRIVERS']['betonlineag'] = betonlineag.open_browser()
        params['DRIVERS']['barstool'] = barstool.open_browser()
        params['DRIVERS']['draftkings'] = draftkings.open_browser()

        return params

    params = initialize_browsers(params)

    start_time_1 = time.time()

    start_time_2 = time.time()

    start_time_3 = time.time()

    running = True

    check_list = []

    count = 0
    
    # load the trained model and scaler
    with open('/Users/stefanfeiler/PycharmProjects/autobet_placer_1/23/SmartBetter_TEST/model/model.pkl', 'rb') as f:
        model, scaler = pickle.load(f)
        params['MODEL'] = model
        params['SCALER'] = scaler

    return params, start_time_1, start_time_2, start_time_3, check_list, count, running

def restart_browsers(params: dict) -> dict:
    params['DRIVERS']['barstool'].quit()
    params['DRIVERS']['draftkings'].quit()
    params['DRIVERS']['betonlineag'].quit()

    params['DRIVERS']['barstool'] = barstool.open_browser()
    params['DRIVERS']['draftkings'] = draftkings.open_browser()
    params['DRIVERS']['betonlineag'] = betonlineag.open_browser()

    return params


def run(check_list):
    # Gather the market data
    market_data = current_odds_getter.get_data(params)
    
    # Make a dict containing all games whose commence_time falls within 2 hours of snapshot_time 
    bettable_games = current_odds_getter.get_list_of_games(params, market_data)
    
    # Makes a simple list of the team names whose games are live
    live_games = current_odds_getter.get_live_games_list(market_data)

    # Make a dict that contains market data for the books we have money in, that has entries by team
    odds_dict = current_odds_getter.make_odds_dict(params, market_data, bettable_games)
    
    params['ODDS DICT'] = odds_dict

    # This compiles and checks all the home teams and then all the away teams data, and returns a dict full of modeled probabilities
    team_probabilities = current_odds_getter.get_market_odds_in_proper_order(market_data, params, bettable_games)

    # Compiles all the work into a dict that contains the EV for each sports book's lines for each game running
    ev_dict = current_odds_getter.make_ev_dict(team_probabilities, odds_dict)

    # Tries to bet the games that should be bet
    place_bets.run(params, ev_dict, check_list, live_games)
    
    time.sleep(5)
    
    print(check_list)


if __name__ == '__main__':

    params, start_time_1, start_time_2, start_time_3, check_list, count, running = initialize(params)

    # Every 5 seconds, run the entire function
    while running:

        # Check if 10 minutes have passed
        if time.time() - start_time_1 > 600:

            start_time_1 = time.time()

            check_list = []

            count +=1

            print(f"Round: {count}")


        # Check if 20 minutes have passed
        elif time.time() - start_time_3 > 1200:

            # Close the bots and re-login to avoid logout-errors
            params = restart_browsers(params)

            barstool.refresh(params['DRIVERS']['barstool'])


            # start a new timer
            start_time_3 = time.time()

            # print
            print("Browsers restarted successfuly")

        run(check_list)

        time.sleep(5)


