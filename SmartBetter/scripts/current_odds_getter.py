import copy
import time
import pickle
import requests
import pandas as pd
from datetime import datetime, timedelta
import util
import torch
from sklearn.preprocessing import OneHotEncoder
#import notification
import numpy as np


young_params = {

    "EXTRA_INFO_SHEET": pd.read_csv('/Users/stefanfeiler/Desktop/SmartBetter/SmartBetter/data/2023_mlb_extra.csv'),

    'min_pred_threshold':19.409,

    "SHEET_HEADER" : ['game_id', 'commence_time', 'time_pulled', 'team_1', 'team_2','barstool_1_odds', 'barstool_1_time', 'barstool_2_odds', 'barstool_2_time', 'betclic_1_odds', 'betclic_1_time', 'betclic_2_odds', 'betclic_2_time', 'betfair_1_odds', 'betfair_1_time', 'betfair_2_odds', 'betfair_2_time', 'betfred_1_odds', 'betfred_1_time', 'betfred_2_odds', 'betfred_2_time', 'betmgm_1_odds', 'betmgm_1_time', 'betmgm_2_odds', 'betmgm_2_time', 'betonlineag_1_odds', 'betonlineag_1_time', 'betonlineag_2_odds', 'betonlineag_2_time', 'betrivers_1_odds', 'betrivers_1_time', 'betrivers_2_odds', 'betrivers_2_time', 'betus_1_odds', 'betus_1_time', 'betus_2_odds', 'betus_2_time', 'betway_1_odds', 'betway_1_time', 'betway_2_odds', 'betway_2_time', 'bovada_1_odds', 'bovada_1_time', 'bovada_2_odds', 'bovada_2_time', 'casumo_1_odds', 'casumo_1_time', 'casumo_2_odds', 'casumo_2_time', 'circasports_1_odds', 'circasports_1_time', 'circasports_2_odds', 'circasports_2_time', 'coral_1_odds', 'coral_1_time', 'coral_2_odds', 'coral_2_time', 'draftkings_1_odds', 'draftkings_1_time', 'draftkings_2_odds', 'draftkings_2_time', 'fanduel_1_odds', 'fanduel_1_time', 'fanduel_2_odds', 'fanduel_2_time', 'foxbet_1_odds', 'foxbet_1_time', 'foxbet_2_odds', 'foxbet_2_time', 'gtbets_1_odds', 'gtbets_1_time', 'gtbets_2_odds', 'gtbets_2_time', 'ladbrokes_1_odds', 'ladbrokes_1_time', 'ladbrokes_2_odds', 'ladbrokes_2_time', 'lowvig_1_odds', 'lowvig_1_time', 'lowvig_2_odds', 'lowvig_2_time', 'marathonbet_1_odds', 'marathonbet_1_time', 'marathonbet_2_odds', 'marathonbet_2_time', 'matchbook_1_odds', 'matchbook_1_time', 'matchbook_2_odds', 'matchbook_2_time', 'mrgreen_1_odds', 'mrgreen_1_time', 'mrgreen_2_odds', 'mrgreen_2_time', 'mybookieag_1_odds', 'mybookieag_1_time', 'mybookieag_2_odds', 'mybookieag_2_time', 'nordicbet_1_odds', 'nordicbet_1_time', 'nordicbet_2_odds', 'nordicbet_2_time', 'onexbet_1_odds', 'onexbet_1_time', 'onexbet_2_odds', 'onexbet_2_time', 'paddypower_1_odds', 'paddypower_1_time', 'paddypower_2_odds', 'paddypower_2_time', 'pinnacle_1_odds', 'pinnacle_1_time', 'pinnacle_2_odds', 'pinnacle_2_time', 'pointsbetus_1_odds', 'pointsbetus_1_time', 'pointsbetus_2_odds', 'pointsbetus_2_time', 'sport888_1_odds', 'sport888_1_time', 'sport888_2_odds', 'sport888_2_time', 'sugarhouse_1_odds', 'sugarhouse_1_time', 'sugarhouse_2_odds', 'sugarhouse_2_time', 'superbook_1_odds', 'superbook_1_time', 'superbook_2_odds', 'superbook_2_time', 'twinspires_1_odds', 'twinspires_1_time', 'twinspires_2_odds', 'twinspires_2_time', 'unibet_1_odds', 'unibet_1_time', 'unibet_2_odds', 'unibet_2_time', 'unibet_eu_1_odds', 'unibet_eu_1_time', 'unibet_eu_2_odds', 'unibet_eu_2_time', 'unibet_uk_1_odds', 'unibet_uk_1_time', 'unibet_uk_2_odds', 'unibet_uk_2_time', 'unibet_us_1_odds', 'unibet_us_1_time', 'unibet_us_2_odds', 'unibet_us_2_time', 'williamhill_1_odds', 'williamhill_1_time', 'williamhill_2_odds', 'williamhill_2_time', 'williamhill_us_1_odds', 'williamhill_us_1_time', 'williamhill_us_2_odds', 'williamhill_us_2_time', 'wynnbet_1_odds', 'wynnbet_1_time', 'wynnbet_2_odds', 'wynnbet_2_time']
}

def init_params(params):
    df = params["EXTRA_INFO_SHEET"]

    params["number_of_game_today_dict"] = dict(zip(df['my_id'], df['number_of_game_today']))

    params["day_of_week_dict"] = dict(zip(df['my_id'], df['day_of_week']))

    params["away_team_dict"] = dict(zip(df['my_id'], df['away_team']))

    params["away_team_league_dict"] = dict(zip(df['my_id'], df['away_team_league']))

    params["away_team_game_number_dict"] = dict(zip(df['my_id'], df['away_team_game_number']))

    params["home_team_dict"] = dict(zip(df['my_id'], df['home_team']))

    params["home_team_league_dict"] = dict(zip(df['my_id'], df['home_team_league']))

    params["home_team_game_number_dict"] = dict(zip(df['my_id'], df['home_team_game_number']))

    params["day_night_dict"] = dict(zip(df['my_id'], df['day_night']))

    params["park_id_dict"] = dict(zip(df['my_id'], df['park_id']))

    # return params
    # Load the encoders from the file
    with open('OddsNet/MODELS/mlb_encoders.pkl', 'rb') as file:
        encoders = pickle.load(file)

    params['encoders'] = encoders

    # Load the scaler from the file
    with open('OddsNet/MODELS/mlb_scaler.pkl', 'rb') as file:
        scaler = pickle.load(file)

    params['scaler'] = scaler
    
    # # TODO: Match the model 
    # model = torch.nn.Sequential(   
    #         torch.nn.Linear(134,256),
    #         torch.nn.SiLU(),
    #         torch.nn.Linear(256,256),
    #         torch.nn.SiLU(),
    #         torch.nn.Linear(256,128),
    #         torch.nn.SiLU(),
    #         torch.nn.Linear(128,64),
    #         torch.nn.SiLU(),
    #         torch.nn.Linear(64,16),
    #         torch.nn.SiLU(),
    #         torch.nn.Linear(16,1)
    #      )
    
    # # TODO: Change this path
    # # Load the saved model state
    # model.load_state_dict(torch.load('OddsNet/MODELS/mlb_model.pth'))

    # params['model'] = model

    return params


def run():

    params = init_params(young_params)

    market_data = util.pull_market_odds(params)

    print('Model initialized')

    while True:

        # Market data is ready to go. Times are adjusted, were ready for combination with the game infomation sheet
        market_data = util.pull_market_odds(params)

        market_data.to_csv('/Users/stefanfeiler/Desktop/test_market_odds.csv')

        raw_data_point = util.make_full_data_point(market_data, params)

        print(raw_data_point)

        for data_point in raw_data_point:
            
            input_tensor = torch.tensor(data_point, dtype=torch.float32)
            output_prediction = params['model'](input_tensor).detach().numpy()[0][0]

            if output_prediction > params['min_pred_threshold']:

                numerical_data = data_point[:, :42]

                american_odds = de_standardize(numerical_data, params)

                team_bet_on = decode('team_1',data_point[:, 44:74], params)
               # notification.notify_model_thresh(team_bet_on, output_prediction, american_odds)

                print(f'{team_bet_on}, {american_odds}')


        time.sleep(300)
        time.sleep(3)
        


    return 
    
def de_standardize(arr, params):

    odds = params['scaler'].inverse_transform(arr)

    barstool_odds = odds[0][0]
    if barstool_odds >= 2.0:
        american_odds = (barstool_odds - 1) * 100
    if barstool_odds < 2.0:
        american_odds = -100 / (barstool_odds - 1)

    return int(american_odds)


def decode(col_name, arr, params):
    return params['encoders'][col_name].inverse_transform(arr)[0][0]

run()
