import json
import operator
import time
from datetime import timedelta
import statistics
import os
from contextlib import redirect_stdout
import warnings
from sklearn.exceptions import DataConversionWarning



import numpy as np
import pandas as pd
import requests
from numpy.ma.bench import timer

import barstool
import betonlineag
import mybookieag
import notification
import fanduel
import draftkings

import tensorflow as tf

# Set warning filter to ignore DataConversionWarning
warnings.filterwarnings("ignore", category=UserWarning)

def get_data(params):
    API_KEY = '6b7c5a1a854ea2d45d5d9d0f958dd3a0'

    SPORT = 'basketball_nba'

    MARKETS = 'h2h'  # h2h | spreads | totals. Multiple can be specified if comma delimited

    ODDS_FORMAT = 'american'

    DATE_FORMAT = 'iso'

    BOOKMAKERS = params["BOOKMAKERS_DATA_STRING"]

    odds_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/',
        params={
            'api_key': API_KEY,
            'markets': MARKETS,
            'oddsFormat': ODDS_FORMAT,
            'dateFormat': DATE_FORMAT,
            'bookmakers': BOOKMAKERS
        }
    )

    if odds_response.status_code != 200:
        print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')

    else:
        odds_json = odds_response.json()

        df = pd.DataFrame.from_dict(odds_json)

        #df.to_csv('/Users/stefanfeiler/Desktop/nfl_testing_odds.csv', mode='a', index=False)

        return odds_json

def get_snapshot_time(data):
    
    times_list = []
        
    for bookmaker_game_data in data['bookmakers']:

        update_time = pd.to_datetime(bookmaker_game_data['markets'][0]['last_update'])

        times_list.append(update_time)
        
    snapshot_time = max(times_list)
        
    return snapshot_time

def get_market_odds_in_proper_order(market_data,params, running_games):

    teams_dict = {}

    ev_dict = {}

    for data in market_data:
        if data['home_team'] in running_games and data['away_team'] in running_games:

            home_team_odds =[]

            away_team_odds =[]

            home_team_odds_if_time_list = []

            away_team_odds_if_time_list = []

            commence_time = data['commence_time']

            commence_time_mst = pd.to_datetime(commence_time) - timedelta(hours=6)

            time_since_game_start = (commence_time_mst.replace(tzinfo=None) - pd.to_datetime(pd.Timestamp.now())).total_seconds()/60

            for bookmaker_game_data in data['bookmakers']:

                snapshot_time = get_snapshot_time(data)

                bookmaker_update_time = pd.to_datetime(bookmaker_game_data['markets'][0]['last_update'])

                if abs(snapshot_time-bookmaker_update_time) <= timedelta(seconds=5):
                    home_team_odds_if_time_list.append(convert_american_to_decimal(bookmaker_game_data['markets'][0]['outcomes'][0]['price']))
                    away_team_odds_if_time_list.append(convert_american_to_decimal(bookmaker_game_data['markets'][0]['outcomes'][1]['price']))


                home_team_dict = {
                }

                away_team_dict = {
                }

                home_team_odds.append((bookmaker_game_data['key'], convert_american_to_decimal(bookmaker_game_data['markets'][0]['outcomes'][0]['price'])))

                away_team_odds.append((bookmaker_game_data['key'], convert_american_to_decimal(bookmaker_game_data['markets'][0]['outcomes'][1]['price'])))

            home_team_dict.update(home_team_odds)

            away_team_dict.update(away_team_odds)

            average_home_odds_if_time = round(average(home_team_odds_if_time_list),4)

            average_away_odds_if_time = round(average(away_team_odds_if_time_list),4)

            home_longshot = get_longshot_variable(average_home_odds_if_time, params)

            away_longshot = get_longshot_variable(average_away_odds_if_time, params)

            home_items = [('market_average_if_time', average_home_odds_if_time), ('time_since_game_start', time_since_game_start),
                          ('longshot_variable', home_longshot)]

            away_items = [('market_average_if_time' , average_away_odds_if_time), ('time_since_game_start', time_since_game_start),
                          ('longshot_variable', away_longshot)]

            home_team_dict.update(home_items)

            away_team_dict.update(away_items)

            home_prob = try_to_assign_values_to_datapoint(home_team_dict, average_home_odds_if_time, params)

            away_prob = try_to_assign_values_to_datapoint(away_team_dict, average_away_odds_if_time, params)

            best_home_odds = max(home_team_odds_if_time_list)

            best_away_odds = max(away_team_odds_if_time_list)

            home_ev = make_modeled_ev(home_prob, best_home_odds)

            away_ev = make_modeled_ev(away_prob, best_away_odds)

            teams_dict.update({(data['home_team'], home_prob)})
            teams_dict.update({(data['away_team'], away_prob)})

            ev_dict.update({(data['home_team'], home_ev)})
            ev_dict.update({(data['away_team'], away_ev)})


    return teams_dict

def make_modeled_ev(modeled_prob, best_available_odds):
    best_available_odds = convert_american_to_decimal(best_available_odds)
    ev = (((100 * best_available_odds)-100) * modeled_prob) - (100 * modeled_prob)
    return ev

def convert_decimal_to_prob(decimal_odds):
    return 1 / decimal_odds

def convert_american_to_decimal(american_odds):
    return round(1 + (abs(american_odds) / 100),3) if american_odds > 0 else round((100 / abs(american_odds)) + 1,3)

def average(lst):
        """Gets the average of of a list of values """
        return sum(lst)/len(lst)

def get_longshot_variable(x, params):
    """Compares the current market average to the mean and std of the annual data"""
    mean = params["ANNUAL_MEAN_DECIMAL_ODDS"]
    std = params['ANNUAL_STD_DECIMAL_ODDS']

    return round(((x - mean) / std),4)

def try_to_assign_values_to_datapoint(data: dict, na_fil, params):
    """Returns the predicted probability of the given team to win"""

    #TODO: CHECK THAT ALL THESE NAMESS ARE KEYS IN THE API PULL
    data_point_dict = {

        'barstool':data['barstool'] if 'barstool' in data else na_fil,
        'betmgm': data['betmgm'] if 'betmgm' in data else na_fil,
        'betonlineag': data['betonlineag'] if 'betonlineag' in data else na_fil,
        'betrivers': data['betrivers'] if 'betrivers' in data else na_fil,
        'bovada': data['bovada'] if 'bovada' in data else na_fil,
        'draftkings': data['draftkings'] if 'draftkings' in data else na_fil,
        'fanduel': data['fanduel'] if 'fanduel' in data else na_fil,
        'foxbet': data['foxbet'] if 'foxbet' in data else na_fil,
        'gtbets': data['gtbets'] if 'gtbets' in data else na_fil,
        'pinnacle': data['pinnacle'] if 'pinnacle' in data else na_fil,
        'pointsbetus': data['pointsbetus'] if 'pointsbetus' in data else na_fil,
        'sugarhouse': data['sugarhouse'] if 'sugarhouse' in data else na_fil,
        'twinspires': data['twinspires'] if 'twinspires' in data else na_fil,
        'unibet': data['unibet'] if 'unibet' in data else na_fil,
        'williamhill_us': data['williamhill_us'] if 'williamhill_us' in data else na_fil,
        'current_market_average_if_time': na_fil,
        'time_since_game_start': data['time_since_game_start'],
        'longshot_variable': data['longshot_variable'],
    }

    # Calculate the standard deviation of the odds data
    stdev = statistics.stdev(list(data_point_dict.values())[:-3])

    # Add the variation to the
    data_point_dict['std_market_odds'] = stdev

    # Define the input shape for the model
    input_shape = (1, 19)

    # Assuming your input data is stored in a dictionary called 'datapoint'
    datapoint_array = np.array(list(data_point_dict.values())).reshape(input_shape)

    # Use the scaler to scale new data
    X_new_scaled = params['SCALER'].transform(datapoint_array)

    with open(os.devnull, 'w') as f:
        with redirect_stdout(f):
            # make predictions using the scaled data and the loaded model
            y_pred = params['MODEL'].predict(X_new_scaled)[0][0]
    return y_pred

def get_live_games_list(data):
    """    Make a simple list of all the games that are actually live, comes in handy later when we need to pass into
    the bet bots if the game is live or upcoming
    """

    list_of_live_games = []

    for each_game in data:
        commence_time = pd.to_datetime(each_game['commence_time'])
        if commence_time.replace(tzinfo=None) - pd.to_datetime(pd.Timestamp.now()) < timedelta(seconds=0):
            list_of_live_games.append(each_game['home_team'])
            list_of_live_games.append(each_game['away_team'])

    return  list_of_live_games

def make_odds_dict(params, data, running_games):

    all_teams_dict = {}

    
    for game_data in data:
        if game_data['home_team'] in running_games and game_data['away_team'] in running_games:

            home_team = game_data['home_team']

            away_team = game_data['away_team']

            home_team_dict = {}

            away_team_dict = {}

            for bookmaker in game_data['bookmakers']:
                if bookmaker['key'] in params['BOOKMAKERS_TO_BET_WITH_LIST']:
                    home_team_data = [(bookmaker['key'], bookmaker['markets'][0]['outcomes'][0]['price'])]
                    away_team_data = [(bookmaker['key'], bookmaker['markets'][0]['outcomes'][1]['price'])]
                    home_team_dict.update(home_team_data)
                    away_team_dict.update(away_team_data)

            all_teams_dict[home_team] = home_team_dict
            all_teams_dict[away_team] = away_team_dict
            
            
    all_teams_dict = sort_dicts(all_teams_dict)

    return all_teams_dict

def get_list_of_games(params, data):
    
    list_of_games = []
    for game_data in data:

        commence_time_mst = pd.to_datetime(game_data['commence_time']) - timedelta(hours=6)

        time_since_game_start = abs((commence_time_mst.replace(tzinfo=None) - pd.to_datetime(
            pd.Timestamp.now())).total_seconds() / 60)

        if time_since_game_start <= params['ABS MINUTES SINCE GAME START']:

            list_of_games.append(game_data['home_team'])
            
            list_of_games.append(game_data['away_team'])
            
    return list_of_games

def make_ev_dict(dict1, dict2):

    result_dict = {}

    for team, prob in dict1.items():



        odds_dict = dict2[team]

        team_result_dict = {}

        for bookmaker, odds in odds_dict.items():
            result = make_modeled_ev(prob, odds)
            # update the team_result_dict with the calculated value
            team_result_dict[bookmaker] = result
        # update the result_dict with the team_result_dict for the current team
        result_dict[team] = team_result_dict

    result_dict = sort_dicts(result_dict)

    return result_dict

def sort_dicts(dict_of_dicts):
    for key in dict_of_dicts:
        sorted_dict = dict(sorted(dict_of_dicts[key].items(), key=lambda item: item[1], reverse=True))
        dict_of_dicts[key] = sorted_dict

    return dict_of_dicts





            






