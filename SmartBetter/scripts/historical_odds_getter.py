import glob
import os
import warnings
from datetime import datetime, timedelta, time

import numpy as np
import pandas as pd

import requests
import util

warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None

# We need to compile a list of every day that there's been an MLB game since June 6, 2020. We need to read that list and store it. Before we pull any historical odds for a given date we need to check to make sure that there were actually games (at least 1) played on that day.

params = {
    "START_DATE": util.get_start_date(),

    "END_DATE": util.get_end_date(),

    "LIST_OF_GAME_DAYS": util.get_list_of_game_days(),

    "SHEET_HEADER" : ['game_id', 'commence_time', 'time_pulled', 'team_1', 'team_2','barstool_1_odds', 'barstool_1_time', 'barstool_2_odds', 'barstool_2_time',      'betclic_1_odds', 'betclic_1_time', 'betclic_2_odds', 'betclic_2_time', 'betfair_1_odds', 'betfair_1_time', 'betfair_2_odds', 'betfair_2_time', 'betfred_1_odds', 'betfred_1_time', 'betfred_2_odds', 'betfred_2_time', 'betmgm_1_odds', 'betmgm_1_time', 'betmgm_2_odds', 'betmgm_2_time', 'betonlineag_1_odds', 'betonlineag_1_time', 'betonlineag_2_odds', 'betonlineag_2_time', 'betrivers_1_odds', 'betrivers_1_time', 'betrivers_2_odds', 'betrivers_2_time', 'betus_1_odds', 'betus_1_time', 'betus_2_odds', 'betus_2_time', 'betway_1_odds', 'betway_1_time', 'betway_2_odds', 'betway_2_time', 'bovada_1_odds', 'bovada_1_time', 'bovada_2_odds', 'bovada_2_time', 'casumo_1_odds', 'casumo_1_time', 'casumo_2_odds', 'casumo_2_time', 'circasports_1_odds', 'circasports_1_time', 'circasports_2_odds', 'circasports_2_time', 'coral_1_odds', 'coral_1_time', 'coral_2_odds', 'coral_2_time', 'draftkings_1_odds', 'draftkings_1_time', 'draftkings_2_odds', 'draftkings_2_time', 'fanduel_1_odds', 'fanduel_1_time', 'fanduel_2_odds', 'fanduel_2_time', 'foxbet_1_odds', 'foxbet_1_time', 'foxbet_2_odds', 'foxbet_2_time', 'gtbets_1_odds', 'gtbets_1_time', 'gtbets_2_odds', 'gtbets_2_time', 'ladbrokes_1_odds', 'ladbrokes_1_time', 'ladbrokes_2_odds', 'ladbrokes_2_time', 'lowvig_1_odds', 'lowvig_1_time', 'lowvig_2_odds', 'lowvig_2_time', 'marathonbet_1_odds', 'marathonbet_1_time', 'marathonbet_2_odds', 'marathonbet_2_time', 'matchbook_1_odds', 'matchbook_1_time', 'matchbook_2_odds', 'matchbook_2_time', 'mrgreen_1_odds', 'mrgreen_1_time', 'mrgreen_2_odds', 'mrgreen_2_time', 'mybookieag_1_odds', 'mybookieag_1_time', 'mybookieag_2_odds', 'mybookieag_2_time', 'nordicbet_1_odds', 'nordicbet_1_time', 'nordicbet_2_odds', 'nordicbet_2_time', 'onexbet_1_odds', 'onexbet_1_time', 'onexbet_2_odds', 'onexbet_2_time', 'paddypower_1_odds', 'paddypower_1_time', 'paddypower_2_odds', 'paddypower_2_time', 'pinnacle_1_odds', 'pinnacle_1_time', 'pinnacle_2_odds', 'pinnacle_2_time', 'pointsbetus_1_odds', 'pointsbetus_1_time', 'pointsbetus_2_odds', 'pointsbetus_2_time', 'sport888_1_odds', 'sport888_1_time', 'sport888_2_odds', 'sport888_2_time', 'sugarhouse_1_odds', 'sugarhouse_1_time', 'sugarhouse_2_odds', 'sugarhouse_2_time', 'superbook_1_odds', 'superbook_1_time', 'superbook_2_odds', 'superbook_2_time', 'twinspires_1_odds', 'twinspires_1_time', 'twinspires_2_odds', 'twinspires_2_time', 'unibet_1_odds', 'unibet_1_time', 'unibet_2_odds', 'unibet_2_time', 'unibet_eu_1_odds', 'unibet_eu_1_time', 'unibet_eu_2_odds', 'unibet_eu_2_time', 'unibet_uk_1_odds', 'unibet_uk_1_time', 'unibet_uk_2_odds', 'unibet_uk_2_time', 'unibet_us_1_odds', 'unibet_us_1_time', 'unibet_us_2_odds', 'unibet_us_2_time', 'williamhill_1_odds', 'williamhill_1_time', 'williamhill_2_odds', 'williamhill_2_time', 'williamhill_us_1_odds', 'williamhill_us_1_time', 'williamhill_us_2_odds', 'williamhill_us_2_time', 'wynnbet_1_odds', 'wynnbet_1_time', 'wynnbet_2_odds', 'wynnbet_2_time'],

    "SCORES_FILE": os.path.join(util.get_data_folder(), 'mlb_extra_stats.csv'),

    "ODDS_RAW": os.path.join(util.get_data_folder(), 'mlb_raw_2.csv')
}

def init():
    return params

def run():
    params = init()
    # Right now, we're only focused on the historical odds and don't care about getting odds from the last time we pulled.

    start_get_odds(params)

def start_get_odds(params):
    # END_DATE is the most recent date, START_DATE is the oldest date we have. Working backwards in calendar time
    sd = params['START_DATE']
    ed = params['END_DATE']
    date = ed

    # While the date we feed is greater than the start date:
    while date > sd:
        # Check the day in the list of days
        date_str = util.get_date_in_score_sheet_format(date)

        if date_str in params["LIST_OF_GAME_DAYS"]:
            # Get the odds and process them
            odds = get_odds(date)
            # Save the previous timestamp as the next date
            date = util.get_api_format_date(odds['previous_timestamp'][0])

        elif date_str not in params["LIST_OF_GAME_DAYS"]:
            # TODO: Fill this in with a new date declaration somehow
            date = date - timedelta(hours=24)

def calculate_acccuracy(df):
    end_date = pd.to_datetime(df['time_pulled'].iloc[-1])
    # end_date = pd.to_datetime(df['time_pulled'].iloc[-1], format='%m/%d/%y %H:%M')
    start_date = end_date - timedelta(days=params['DAYS'])

    best_bookmaker = ''
    best_bookmaker_score = 0

    # mask so that we're only working w the right rows
    # then calculate the mean of every other row or whatever
    # Make a copy of the original DataFrame

    df['time_pulled'] = pd.to_datetime(df['time_pulled'])

    mask = (df['time_pulled'] > start_date) & (df['time_pulled'] <= end_date)
    masked_df = df[mask]


    for col in masked_df.columns:
        if col.endswith("_1_prob"):
            masked_df[col] = np.where(masked_df["team_1"] == masked_df["winning_team"], masked_df[col], 0)
            bookmaker = col.split('_')[0]
            #print(f"{bookmaker}: {masked_df[col].mean()}")
            if masked_df[col].mean() > best_bookmaker_score:
                best_bookmaker = bookmaker
                best_bookmaker_score = masked_df[col].mean()

    return best_bookmaker

def map_winning_teams(df1, df2):
    # Merge the two dataframes on the 'id' column
    df2['winning_team'] = df2['my_id'].map(df1.set_index('my_id')['winning_team'])
    df2.drop(columns=df2.columns[df2.columns.str.contains('Unnamed')], axis=1)

    # Drop all the rows representing games that haven't happened yet
    df2 = df2.dropna(subset=["winning_team"])
    return df2

def format_scores_file(df):
    # Only continue with the data frame that actually contains games that have finished
    df = df.dropna(subset=["PTS"])

    # Convert the data into "my_id" column
    df = make_my_id_scores(df)

    df = make_winning_team(df)

    return df

def make_my_id_scores(df):
    # Convert the date column to a datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%a, %b %d, %Y')

    conditions = [
        df['Visitor/Neutral'].astype(str) < df['Home/Neutral'].astype(str),
        df['Visitor/Neutral'].astype(str) > df['Home/Neutral'].astype(str)
    ]

    choices = [
        df['Visitor/Neutral'].astype(str) + df['Home/Neutral'].astype(str) + df['Date'].dt.month.astype(
            str) + df['Date'].dt.day.astype(str) + df['Date'].dt.year.astype(str),
        df['Home/Neutral'].astype(str) + df['Visitor/Neutral'].astype(str) + df['Date'].dt.month.astype(
            str) + df['Date'].dt.day.astype(str) + df['Date'].dt.year.astype(str)
    ]

    df['my_id'] = np.select(conditions, choices, default=np.nan)

    return df

def format_odds_file(df2):

    # Convert the commence time to a datetime
    # removed format
    df2['commence_time'] = pd.to_datetime(df2['commence_time'])

    # Subtract 5 hours from commence_time to get commence_time_est
    df2['commence_time_est'] = df2['commence_time'] - timedelta(hours=5)

    # Create the my_id column
    df2 = make_my_id_odds(df2)

    # Convert odds to probabilities
    for col in df2.columns:
        if col.endswith("1_odds"):
            bookmaker = col.split('_')[0]
            right_odds_index = df2.columns.get_loc(col) + 2
            right_2_col = df2.columns[right_odds_index]
            df2[[f"{bookmaker}_1_prob", f"{bookmaker}_2_prob"]] = df2.apply(
                lambda row: calc_fair_odds(row[col], row[right_2_col]), axis=1,
                result_type='expand')

    # df2['time_pulled'] = pd.to_datetime(df2['time_pulled'], )
    # df2['time_pulled'] = df2['time_pulled'].dt.strftime("%m/%d/%Y %I:%M:%S %p")
    return df2

def calc_fair_odds(num1, num2):
    if not pd.isna(num1) and not pd.isna(num2):
        num1 = int(num1)
        num2 = int(num2)
        if num1 > 0 and num2 < 0:
            dividend = 100 / (100 + num1)
            divisor = ((abs(num2) / (abs(num2) + 100)) + dividend)
            return dividend / divisor, 1 - (dividend / divisor)
        elif num1 < 0 and num2 > 0:
            dividend = abs(num1) / (abs(num1) + 100)
            divisor = ((100 / (100 + num2)) + dividend)
            return dividend / divisor, 1 - (dividend / divisor)

        elif num1 > 0 and num2 > 0:
            dividend = 100 / (100 + num1)
            divisor = (dividend + (100 / 100 + num2))
            return dividend / divisor, 1 - (dividend / divisor)

        elif num1 < 0 and num2 < 0:
            dividend = abs(num1) / (abs(num1) + 100)
            divisor = (dividend + (abs(num2) / (abs(num2) + 100)))
            return dividend / divisor, 1 - (dividend / divisor)
    else:
        return np.nan, np.nan

def make_my_id_odds(df):
    df['commence_time_est'] = pd.to_datetime(df['commence_time_est'], format="%m/%d/%Y %I:%M:%S %p")

    conditions = [
        df['team_1'].astype(str) < df['team_2'].astype(str),
        df['team_2'].astype(str) > df['team_1'].astype(str)
    ]

    choices = [
        df['team_1'].astype(str) + df['team_2'].astype(str) + df['commence_time_est'].dt.month.astype(
            str) + df['commence_time_est'].dt.day.astype(str) + df['commence_time_est'].dt.year.astype(str),
        df['team_2'].astype(str) + df['team_1'].astype(str) + df['commence_time_est'].dt.month.astype(
            str) + df['commence_time_est'].dt.day.astype(str) + df['commence_time_est'].dt.year.astype(str),
    ]

    df['my_id'] = np.select(conditions, choices, default=np.nan)

    return df

def make_winning_team(df):
    conditions = [
        df.iloc[:, 3] > df.iloc[:, 5],
        df.iloc[:, 5] > df.iloc[:, 3]
    ]

    choices = [
        df.iloc[:, 2],
        df.iloc[:, 4]
    ]

    df["winning_team"] = np.select(conditions, choices, default=np.nan)

    return df

def get_odds(d):
    API_KEY = '02456682ed7b05ec7fd159a594d48339'

    SPORT = 'baseball_mlb'

    REGIONS = 'us,eu,uk'

    MARKETS = 'h2h' 

    ODDS_FORMAT = 'decimal'  # decimal | american

    DATE_FORMAT = 'iso'

    DATE = util.get_api_format_date(d)

    odds_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds-history/',
        params={
            'api_key': API_KEY,
            'regions': REGIONS,
            'markets': MARKETS,
            'oddsFormat': ODDS_FORMAT,
            'dateFormat': DATE_FORMAT,
            'date': DATE,
        }
    )

    if odds_response.status_code != 200:
        print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')
    else:
        odds_json = odds_response.json()

        # Check the usage quota if the date is a new day
        if util.check_if_new_day(d):
            print(f"Date: {d}")
            print(f"Remaining requests: {odds_response.headers['x-requests-remaining']} Used requests: {odds_response.headers['x-requests-used']}")

        # Make a dataframe from this pull
        df = pd.DataFrame.from_dict(odds_json)

        # Process this data
        process_snapshot(df['data'].items(), d, params)

        return df

def process_snapshot(df, date, params):
    
    my_dict = {value: '' for value in params["SHEET_HEADER"]}

    for game in df:
        # Information about the game
        my_dict['game_id'] = game[1]['id']
        my_dict['commence_time'] = util.format_time(game[1]['commence_time'])
        my_dict['time_pulled'] = util.format_time(date)

        # Compiles each bookmakers lines into a dictionary and then appends that row to a df
        for bookie in game[1]['bookmakers']:
            # Get team name
            my_dict['team_1'] = bookie['markets'][0]['outcomes'][0]['name']
            my_dict['team_2'] = bookie['markets'][0]['outcomes'][1]['name']

            # Find the appropriate column
            my_dict[bookie['key'] + "_1_odds"] = bookie['markets'][0]['outcomes'][0]['price']
            my_dict[bookie['key'] + "_1_time"] = util.format_time(bookie['last_update'])

            my_dict[bookie['key'] + "_2_odds"] = bookie['markets'][0]['outcomes'][1]['price']
            my_dict[bookie['key'] + "_2_time"] = util.format_time(bookie['last_update'])

        game_df = pd.DataFrame.from_dict(my_dict, orient='index').T

        game_df.to_csv(params['ODDS_RAW'], mode='a', header=False, index=False)

        my_dict = {}

    return

def update_odds_sheet(df):
    # Drop all the rows representing games that haven't happened yet and all the wierd cases
    df = df.dropna(subset=["time_pulled"])

    # Get the last value in the time_pulled column, AKA the most recent data point
    starting_date = df['time_pulled'].iloc[-1]

    ending_date = datetime.now().isoformat()

    start_get_odds(starting_date, ending_date)

run()
