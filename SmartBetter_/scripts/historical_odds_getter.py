import os
import warnings
from datetime import datetime, timedelta, time

import numpy as np
import pandas as pd

import requests

warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None


params = {
    "DAYS_TO_RUN": 7,
    "HOURS_TO_CHECK": [21, 22, 23, 24, 1, 2, 3, 4, 5, 6, 7],
    "BOOKMAKERS_LIST": [
        "barstool", "betfair", "betmgm", "betonlineag", "betrivers", "bovada", "circasports", "draftkings", "fanduel",
        "mybookieag"
        "foxbet", "gtbets", "pinnacle", "pointsbetus", "sugarhouse", "twinspires", "unibet_us", "williamhill_us",
        "wynnbet", "superbook", "lowvig", "betus"
    ],
    'BOOKMAKERS_TO_SCAN':["draftkings", "betonlineag"],
    "SCORES_PATHNAME": f"../data/scores.xlsx",
    "ODDS_PATHNAME": f"../data/historical_odds.csv",
    "DAYS": 7
}


def run():
    # First we want to check the status of the historical odds we have on file to see if they're up to date.
    # Open the historical odds sheet
    odds_df = pd.read_csv(params["ODDS_PATHNAME"], on_bad_lines='skip', skip_blank_lines=True, low_memory=False)
    odds_df.to_csv(params['ODDS_PATHNAME'], index=False)

    # Check the historical odds sheet to see if we need to update it since the most recent time_pulled. This will
    # append new odds onto the odds sheet
    print("Updating the odds data")
    print("Calculating the accuracy of the bookmakers")
    update_odds_sheet(odds_df)

    odds_df.replace('[]', np.nan, inplace=True)

    # Format the odds_df so that we have the my_id column and the probabilities columns
    odds_df = format_odds_file(odds_df)

    # Open the file containing recent scores
    scores_df = pd.read_excel(params["SCORES_PATHNAME"])

    # Format the scores_df so we have the my_id column as well as the winning_team column
    scores_df = format_scores_file(scores_df)

    # Map the winning team to a new column on the odds_df
    odds_df = map_winning_teams(scores_df, odds_df)

    # Make the accuracy columms and calculate the bookmaker with the best accuracy over the last x days
    accurate_bookmaker = calculate_acccuracy(odds_df)

    return accurate_bookmaker

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


def start_get_odds(sd, ed):
    sd = pd.to_datetime(sd)
    ed = pd.to_datetime(ed)
    date = sd
    i = 0
    while date < ed:
        date = date + timedelta(minutes=10)
        hour = get_hour(date)
        if hour in params['HOURS_TO_CHECK']:
            i += 1
            date_iso = date.isoformat() + "Z"
            get_odds(date_iso, i)


def get_odds(d, i):
    # An api key is emailed to you when you sign up to a plan
    # Get a free API key at https://api.the-odds-api.com/
    API_KEY = '6b7c5a1a854ea2d45d5d9d0f958dd3a0'

    SPORT = 'basketball_nba'  # use the sport_key from the /sports endpoint below, or use 'upcoming' to see the next 8 games across all sports

    REGIONS = 'us,eu'  # uk | us | eu | au. Multiple can be specified if comma delimited

    MARKETS = 'h2h'  # h2h | spreads | totals. Multiple can be specified if comma delimited

    ODDS_FORMAT = 'american'  # decimal | american

    DATE_FORMAT = 'iso'  # iso | unix

    DATE = d

    BOOKMAKERS = "barstool,betfair,betmgm,betonlineag,betrivers,bovada,circasports,draftkings,fanduel,foxbet,gtbets," \
                 "pinnacle,pointsbetus,sugarhouse,twinspires,unibet,williamhill_us,wynnbet"

    odds_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds-history/',
        params={
            'api_key': API_KEY,
            'regions': REGIONS,
            'markets': MARKETS,
            'oddsFormat': ODDS_FORMAT,
            'dateFormat': DATE_FORMAT,
            'date': DATE,
            'bookmakers': BOOKMAKERS
        }
    )

    if odds_response.status_code != 200:
        print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')

    else:
        odds_json = odds_response.json()

        # Check the usage quota
        if i % 720 == 0:
            print('Remaining requests', odds_response.headers['x-requests-remaining'])
            print('Used requests', odds_response.headers['x-requests-used'])
            print(d)

        df = pd.DataFrame.from_dict(odds_json)

        each_game_odds_data(df['data'].items(), d, i)

        return 0


def calc_profit(num):
    if num > 0:
        return num
    else:
        return (100 / abs(num)) * 100


def calc_ev(fair_win_prob, prof, odds_taken):
    if odds_taken > 0:
        stake = 100
    elif odds_taken < 0:
        stake = abs(odds_taken)

    return (fair_win_prob * prof) - ((1 - fair_win_prob) * stake)


def each_game_odds_data(df, d, i):
    values_list = ["game_id", "commence_time", "time_pulled", "team_1", "team_2", "barstool_1_odds", "barstool_1_time",
                   "barstool_2_odds", "barstool_2_time", "betfair_1_odds", "betfair_1_time", "betfair_2_odds",
                   "betfair_2_time", "betmgm_1_odds", "betmgm_1_time", "betmgm_2_odds", "betmgm_2_time",
                   "betonlineag_1_odds", "betonlineag_1_time", "betonlineag_2_odds", "betonlineag_2_time",
                   "betrivers_1_odds", "betrivers_1_time", "betrivers_2_odds", "betrivers_2_time", "bovada_1_odds",
                   "bovada_1_time", "bovada_2_odds", "bovada_2_time", "circasports_1_odds", "circasports_1_time",
                   "circasports_2_odds", "circasports_2_time", "draftkings_1_odds", "draftkings_1_time",
                   "draftkings_2_odds", "draftkings_2_time", "fanduel_1_odds", "fanduel_1_time", "fanduel_2_odds",
                   "fanduel_2_time", "foxbet_1_odds", "foxbet_1_time", "foxbet_2_odds", "foxbet_2_time",
                   "gtbets_1_odds", "gtbets_1_time", "gtbets_2_odds", "gtbets_2_time", "pinnacle_1_odds",
                   "pinnacle_1_time", "pinnacle_2_odds", "pinnacle_2_time", "pointsbetus_1_odds", "pointsbetus_1_time",
                   "pointsbetus_2_odds", "pointsbetus_2_time", "sugarhouse_1_odds", "sugarhouse_1_time",
                   "sugarhouse_2_odds", "sugarhouse_2_time", "twinspires_1_odds", "twinspires_1_time",
                   "twinspires_2_odds", "twinspires_2_time", "unibet_1_odds", "unibet_1_time", "unibet_2_odds",
                   "unibet_2_time", "williamhill_us_1_odds", "williamhill_us_1_time", "williamhill_us_2_odds",
                   "williamhill_us_2_time", "wynnbet_1_odds", "wynnbet_1_time", "wynnbet_2_odds", "wynnbet_2_time"]
    my_dict = {value: '' for value in values_list}


    for game in df:
        # Information about the game
        my_dict['game_id'] = game[1]['id']
        my_dict['commence_time'] = format_time(game[1]['commence_time'])
        my_dict['time_pulled'] = format_time(d)

        # Compiles each bookmakers lines into a dictionary and then appends that row to a df
        for bookie in game[1]['bookmakers']:
            if bookie['key'] in params['BOOKMAKERS_LIST']:
                # Get team name
                my_dict['team_1'] = bookie['markets'][0]['outcomes'][0]['name']
                my_dict['team_2'] = bookie['markets'][0]['outcomes'][1]['name']

                # Find the appropriate column
                my_dict[bookie['key'] + "_1_odds"] = bookie['markets'][0]['outcomes'][0]['price']
                my_dict[bookie['key'] + "_1_time"] = format_time(bookie['last_update'])

                my_dict[bookie['key'] + "_2_odds"] = bookie['markets'][0]['outcomes'][1]['price']
                my_dict[bookie['key'] + "_2_time"] = format_time(bookie['last_update'])

        df2 = pd.DataFrame.from_dict(my_dict, orient='index').T

        df2.to_csv(params['ODDS_PATHNAME'], mode='a', header=False, index=False)

    return


def get_hour(fd):
    date_string = str(fd)
    time = date_string.split(" ")[1]
    hour = int(time.split(":")[0])

    return hour


def format_time(dt):
    return dt.split('T')[0] + " " + dt.split('T')[1][:-1]


def update_odds_sheet(df):
    # Drop all the rows representing games that haven't happened yet and all the wierd cases
    df = df.dropna(subset=["time_pulled"])

    # Get the last value in the time_pulled column, AKA the most recent data point
    starting_date = df['time_pulled'].iloc[-1]

    ending_date = datetime.now().isoformat()

    start_get_odds(starting_date, ending_date)


if __name__ == '__main__':
    run()
