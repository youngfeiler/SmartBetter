from datetime import datetime, timedelta, time
import pandas as pd
import json
import os
import requests
import numpy as np


def pull_market_odds(params):
  API_KEY = '02456682ed7b05ec7fd159a594d48339'

  SPORT = 'baseball_mlb'

  MARKETS = 'h2h'  

  REGIONS = 'us,eu,uk'

  ODDS_FORMAT = 'decimal'

  DATE_FORMAT = 'iso'

  odds_response = requests.get(
    f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/',
    params={
        'api_key': API_KEY,
        'markets': MARKETS,
        'oddsFormat': ODDS_FORMAT,
        'dateFormat': DATE_FORMAT,
        'regions': REGIONS
    }
  )

  if odds_response.status_code != 200:
    print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')

  else:


    odds_json = odds_response.json()

    df = pd.DataFrame.from_dict(odds_json)



    return process_live_odds(df, params)

  
def process_live_odds(df, params):

    my_dict = {value: '' for value in params["SHEET_HEADER"]}

    return_df = pd.DataFrame()
    
    # For each game
    for index, row in df.iterrows():
        # Find the static information
        my_dict['game_id'] = row['id']

        my_dict['commence_time'] = datetime.strptime(str(row['commence_time']), "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=7)

        date = my_dict['commence_time'].strftime('%Y%m%d')

        my_dict['my_id'] = row['home_team'] + row['away_team'] + date

        my_dict['time_pulled'] = ''
        my_dict['team_1'] = row['home_team']
        my_dict['team_2'] = row['away_team']

        bookmakers = row[6]

        # For each bookie
        for bookie in bookmakers:
            
            bookie_column_name = bookie['key'] + "_1_odds"
            if bookie_column_name in params["SHEET_HEADER"]:
                # If the name of the team == the name assigned to team_1:
                if bookie['markets'][0]['outcomes'][0]['name'] == row['home_team']:
                    my_dict[bookie['key'] + "_1_odds"] = bookie['markets'][0]['outcomes'][0]['price']
                    my_dict[bookie['key'] + "_2_odds"] = bookie['markets'][0]['outcomes'][1]['price']

                    my_dict[bookie['key'] + "_1_time"] = datetime.strptime(format_time(bookie['last_update']), "%Y-%m-%d %H:%M:%S") - timedelta(hours=7)
                    my_dict[bookie['key'] + "_2_time"] = datetime.strptime(format_time(bookie['last_update']), "%Y-%m-%d %H:%M:%S") - timedelta(hours=7)
                # If the name of the team == the name assigned to team_2:
                elif bookie['markets'][0]['outcomes'][0]['name'] == row['away_team']:
                    my_dict[bookie['key'] + "_2_odds"] = bookie['markets'][0]['outcomes'][0]['price']
                    my_dict[bookie['key'] + "_1_odds"] = bookie['markets'][0]['outcomes'][1]['price']

                    my_dict[bookie['key'] + "_1_time"] = datetime.strptime(format_time(bookie['last_update']), "%Y-%m-%d %H:%M:%S") - timedelta(hours=7)
                    my_dict[bookie['key'] + "_2_time"] = datetime.strptime(format_time(bookie['last_update']), "%Y-%m-%d %H:%M:%S") - timedelta(hours=7)

        game_df = pd.DataFrame.from_dict(my_dict, orient='index').T

        return_df = pd.concat([return_df, game_df], axis=0)

        my_dict = {}

        return_df.to_csv('/Users/stefanfeiler/Desktop/test_df.csv')

    return return_df


def make_full_data_point(pull_df, params):

    # Map values from column 'B' in df1 to column 'D' based on the mapping dictionary
    pull_df['number_of_game_today'] = pull_df['my_id'].map(params["number_of_game_today_dict"])

    pull_df['day_of_week'] = pull_df['my_id'].map(params['day_of_week_dict'])

    pull_df['away_team'] = pull_df['my_id'].map(params['away_team_dict'])

    pull_df['away_team_league'] = pull_df['my_id'].map(params['away_team_league_dict'])

    pull_df['away_team_game_number'] = pull_df['my_id'].map(params['away_team_game_number_dict'])

    pull_df['home_team'] = pull_df['my_id'].map(params['home_team_dict'])

    pull_df['home_team_league'] = pull_df['my_id'].map(params['home_team_league_dict'])

    pull_df['home_team_game_number'] = pull_df['my_id'].map(params['home_team_game_number_dict'])

    pull_df['day_night'] = pull_df['my_id'].map(params['day_night_dict'])

    pull_df['park_id'] = pull_df['my_id'].map(params['park_id_dict'])

    pull_df.to_csv('/Users/stefanfeiler/Desktop/test_mapped_vals.csv')

    datapoint = pipeline(pull_df, params)

    return datapoint

def pipeline(df, params):
    # Read the column names 
    all_columns = df.columns
    columns = all_columns[5:]
    info_columns = ['game_id', 'commence_time', 'time_pulled', 'home_team', 'away_team', 'team_1', 'team_2']

    odds_columns = [x for x in columns if x.endswith('_odds')]

    time_columns = [x for x in columns if x.endswith('_time')]

    categorical_columns = ['day_of_week', 'away_team_league', 'home_team_league', 'day_night', 'park_id']

    numerical_columns = ['number_of_game_today', 'away_team_game_number', 'home_team_game_number',]

    for col in odds_columns:
        df[col] = df[col].replace(np.nan, 0)
        df[col] = df[col].replace('', 0)
        df[col] = df[col].astype('float64')
    # Replace all the missing time values with Jan 1, 1970
    for col in time_columns:
        df[col] = df[col].replace(np.nan, '1/1/1970 00:00:00')
    for col in time_columns:
        df[col] = pd.to_datetime(df[col])
    df['snapshot_time_taken'] = df[time_columns].apply(lambda x: max(x), axis=1)
    # We need to use that column as the time_pulled variable rather than the actual time pulled 
    df['snapshot_time_taken'] = pd.to_datetime(df['snapshot_time_taken'])
    df['commence_time'] = pd.to_datetime(df['commence_time'])

    df['minutes_since_commence'] = (df['snapshot_time_taken'] - df['commence_time']).dt.total_seconds()/60

    df['hour_of_start'] = df['commence_time'].dt.hour

    # TODO: Make this a param
    new_data = df[df['minutes_since_commence'] >= -360]

    # Select the first subset:
    cols_with_one = [col for col in new_data.columns if '_1' in col]
    cols_with_two = [col for col in new_data.columns if '_2' in col]
    extra_cols = ['game_id', 'commence_time', 'time_pulled', 'home_team', 'away_team', 'number_of_game_today', 'day_of_week', 'away_team_league', 'away_team_game_number', 'home_team_league', 'home_team_game_number', 'day_night', 'park_id', 'minutes_since_commence', 'snapshot_time_taken', 'hour_of_start']

    for each in extra_cols:
        cols_with_one.append(each)
        cols_with_two.append(each)

    df1 = new_data[cols_with_one]
    df2 = new_data[cols_with_two]

    # # Get list of column names from df1
    df1_cols = df1.columns.tolist()

    # # Create dictionary to map column names in df2 to column names in df1
    col_map = {col: df1_cols[i] for i, col in enumerate(df2.columns)}

    # # Rename columns in df2 using dictionary
    df2 = df2.rename(columns=col_map)

    # Concatenate the subsets vertically
    df_stacked = pd.concat([df1, df2], axis=0, ignore_index=True)

    # Reset the index of the new DataFrame
    df_stacked = df_stacked.reset_index(drop=True)
    df_stacked['this_team_league'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], df_stacked['home_team_league'], df_stacked['away_team_league'])

    df_stacked['opponent_league'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], df_stacked['away_team_league'], df_stacked['home_team_league'])

    df_stacked['this_team_game_of_season'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], df_stacked['home_team_game_number'], df_stacked['away_team_game_number'])

    df_stacked['opponent_game_of_season'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], df_stacked['away_team_game_number'], df_stacked['home_team_game_number'])

    df_stacked['home_away'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], 1, 0)

    df['snapshot_time'] = df['snapshot_time_taken'].dt.time

    cols_to_drop=['commence_time', 'time_pulled', 'home_team', 'away_team', 'away_team_league', 'away_team_game_number','home_team_league', 'home_team_game_number', 'snapshot_time_taken']

    result = df_stacked.drop(columns=cols_to_drop)

    df_stacked.to_csv('/Users/stefanfeiler/Desktop/test_live_stacked.csv')

    datapoint = finalize_datapoint(result, params)

    return datapoint

def finalize_datapoint(df, params):

    final_data_points = []

    # DON'T TOUCH. ORDER IS VERY IMPORTANT
    continuous_cols = [col for col in df.columns if '_odds' in col]
    continuous_cols.append('minutes_since_commence')
    continuous_cols.append('this_team_game_of_season')
    continuous_cols.append('opponent_game_of_season')
    categorical_cols = ['home_away', 'team_1', 'hour_of_start', 'day_of_week', 'number_of_game_today', 'day_night', 'park_id', 'this_team_league', 'opponent_league']
    df['number_of_game_today'] = df['number_of_game_today'].astype(int)
    
    for i in range(len(df)):
        new_df = pd.DataFrame()
        dp_raw = pd.DataFrame()
        new_df = pd.DataFrame([df.iloc[i]], columns=df.columns)
        
        dp_raw = pd.concat([new_df[continuous_cols], new_df[categorical_cols]], axis=1)

        dp_raw_np = np.array(dp_raw)


        # Define the indices of the columns you want to standardize and those we don't
        continuous_vars = dp_raw_np[:, :42]
        categorical_vars = dp_raw_np[:, 42:]

        # Create an instance of StandardScaler and fit it on the input data
        scaled_continuous = params['scaler'].transform(continuous_vars)

        one_hot_encoded_row = []
        for i, col_name in enumerate(categorical_cols):
            value = categorical_vars[0][i]
            encoder = params['encoders'][col_name]  # Get the corresponding encoder
            if value == 'DYE01' or value == 'WIL02':
                value = 'LOS03'

            encoded_value = encoder.transform([[value]])  # Pass a 2D array-like input
            one_hot_encoded_row.append(encoded_value)

        one_hot_encoded_row = np.concatenate(one_hot_encoded_row, axis=1)  # Combine encoded values

        final_data_point = np.concatenate((scaled_continuous, one_hot_encoded_row), axis=1)

        final_data_points.append(final_data_point)

    return final_data_points

def get_hour(fd):
    '''
  Function: get_hour(fd)

  Description:
  This function takes in a date (fd) and extracts the hour from it. The input date is expected to be in string format. The function returns the extracted hour as an integer.

  Parameters:

  fd: The input date in string format.
  Returns:

  hour: The extracted hour as an integer.
  Example Usage:
  fd = "2023-06-12 15:30:45"
  hour = get_hour(fd)
  print(hour) # Output: 15
  '''
    date_string = str(fd)
    time = date_string.split(" ")[1]
    hour = int(time.split(":")[0])

    return hour
  
# TODO: Need to rework this to return a pd.datetime probably wold be best.
def format_time(time_string, input_format="%Y-%m-%dT%H:%M:%SZ", output_format="%Y-%m-%d %H:%M:%S"):
    if isinstance(time_string, str):
        datetime_obj = datetime.strptime(time_string, input_format)
    else:
        datetime_obj = time_string

    output_time_string = datetime_obj.strftime(output_format)
    return output_time_string


def calc_payout(dec_odds, profit_only: False):
    '''
Function: calc_payout(dec_odds, profit_only: False)

Description:
This function calculates the payout of the bet based on the given decimal odds (dec_odds). Specify 'True' in the second parameter to be returned only the profit.

Parameters:

dec_odds: The input decimal odds for which the payout is calculated.
profit_only: Default set to false. Specify 'True' to have the stake removed. 

Returns:
payout: The payout in dollars on a $100 bet on these odds.

Example Usage:
odds = 1.2
payout = calc_payout(odds)
print(payout) # Output: 120

odds = 1.2
payout = calc_payout(odds)
print(payout, True) # Output: 20
'''

# TODO: need to convert this to work for decimal odds. Need to document as well.
def calc_ev(fair_win_prob, prof, odds_taken):
    if odds_taken > 0:
        stake = 100
    elif odds_taken < 0:
        stake = abs(odds_taken)

    return (fair_win_prob * prof) - ((1 - fair_win_prob) * stake)

# TODO: Document this
def get_end_date():
    # Starting 5 days after the world series ended such that we can be sure we're getting the earliest snapshot of that last game played
    date_string = "2021-10-10T15:55:00Z"

    datetime_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")

    return datetime_obj

def get_start_date():
    date_string = "2020-06-06T00:00:00Z"

    # Format to the api date 
    datetime_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")

    return datetime_obj

def get_data_folder():
    # Get the current directory
    current_directory = os.getcwd()

    # Get the parent directory
    parent_directory = os.path.dirname(current_directory)

    # Define the path to the desired folder in the parent directory
    folder_path = os.path.join(parent_directory, 'data')

    

    return folder_path

def get_date_in_score_sheet_format(d):

    # Format the datetime object in the desired format
    date_string = int(d.strftime("%Y%m%d"))

    return date_string

def get_list_of_game_days():
    
    data_folder = get_data_folder()

    mlb_scoring_data = os.path.join(data_folder, 'mlb_extra_stats.csv')

    df = pd.read_csv(mlb_scoring_data)

    unique_dates = list(df['date'].unique())

    return unique_dates

def check_if_new_day(datetime_obj):

    hour = datetime_obj.strftime("%H")
    minute = datetime_obj.strftime("%M")


    if (hour == "00" and minute == "05") or (hour == "00" and minute == "00"):
        return True
    else:
        return False
  
def get_api_format_date(d):
    # Convert the original date string to a datetime object
    #original_datetime = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
    # Convert the datetime object to the desired format
    if type(d) == str:
      formatted_date_string = datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ")    
    else:
      formatted_date_string = d.strftime("%Y-%m-%dT%H:%M:%SZ")

    return formatted_date_string

def find_boookmakers(string):
    json_string = json.loads(string)
    bookmakers_data = json_string['data'][0]['bookmakers']
    my_list = []
    for each in bookmakers_data:
        my_list.append(each['key']+'_1_odds')
        my_list.append(each['key']+'_1_time')
        my_list.append(each['key']+'_2_odds')
        my_list.append(each['key']+'_2_time')
    

def make_all_column_names(*lists):
    unique_elements = set()
    for lst in lists:
        unique_elements.update(lst)
    unique_list = list(unique_elements)
    

def order_list_alphabetically(input_list):
    sorted_list = sorted(input_list)
    return sorted_list

def open_csv(file):
    import pandas as pd

values_list = ['barstool_1_odds', 'barstool_1_time', 'barstool_2_odds', 'barstool_2_time', 'betclic_1_odds', 'betclic_1_time', 'betclic_2_odds', 'betclic_2_time', 'betfair_1_odds', 'betfair_1_time', 'betfair_2_odds', 'betfair_2_time', 'betfred_1_odds', 'betfred_1_time', 'betfred_2_odds', 'betfred_2_time', 'betmgm_1_odds', 'betmgm_1_time', 'betmgm_2_odds', 'betmgm_2_time', 'betonlineag_1_odds', 'betonlineag_1_time', 'betonlineag_2_odds', 'betonlineag_2_time', 'betrivers_1_odds', 'betrivers_1_time', 'betrivers_2_odds', 'betrivers_2_time', 'betus_1_odds', 'betus_1_time', 'betus_2_odds', 'betus_2_time', 'betway_1_odds', 'betway_1_time', 'betway_2_odds', 'betway_2_time', 'bovada_1_odds', 'bovada_1_time', 'bovada_2_odds', 'bovada_2_time', 'casumo_1_odds', 'casumo_1_time', 'casumo_2_odds', 'casumo_2_time', 'circasports_1_odds', 'circasports_1_time', 'circasports_2_odds', 'circasports_2_time', 'coral_1_odds', 'coral_1_time', 'coral_2_odds', 'coral_2_time', 'draftkings_1_odds', 'draftkings_1_time', 'draftkings_2_odds', 'draftkings_2_time', 'fanduel_1_odds', 'fanduel_1_time', 'fanduel_2_odds', 'fanduel_2_time', 'foxbet_1_odds', 'foxbet_1_time', 'foxbet_2_odds', 'foxbet_2_time', 'gtbets_1_odds', 'gtbets_1_time', 'gtbets_2_odds', 'gtbets_2_time', 'ladbrokes_1_odds', 'ladbrokes_1_time', 'ladbrokes_2_odds', 'ladbrokes_2_time', 'lowvig_1_odds', 'lowvig_1_time', 'lowvig_2_odds', 'lowvig_2_time', 'marathonbet_1_odds', 'marathonbet_1_time', 'marathonbet_2_odds', 'marathonbet_2_time', 'matchbook_1_odds', 'matchbook_1_time', 'matchbook_2_odds', 'matchbook_2_time', 'mrgreen_1_odds', 'mrgreen_1_time', 'mrgreen_2_odds', 'mrgreen_2_time', 'mybookieag_1_odds', 'mybookieag_1_time', 'mybookieag_2_odds', 'mybookieag_2_time', 'nordicbet_1_odds', 'nordicbet_1_time', 'nordicbet_2_odds', 'nordicbet_2_time', 'onexbet_1_odds', 'onexbet_1_time', 'onexbet_2_odds', 'onexbet_2_time', 'paddypower_1_odds', 'paddypower_1_time', 'paddypower_2_odds', 'paddypower_2_time', 'pinnacle_1_odds', 'pinnacle_1_time', 'pinnacle_2_odds', 'pinnacle_2_time', 'pointsbetus_1_odds', 'pointsbetus_1_time', 'pointsbetus_2_odds', 'pointsbetus_2_time', 'sport888_1_odds', 'sport888_1_time', 'sport888_2_odds', 'sport888_2_time', 'sugarhouse_1_odds', 'sugarhouse_1_time', 'sugarhouse_2_odds', 'sugarhouse_2_time', 'superbook_1_odds', 'superbook_1_time', 'superbook_2_odds', 'superbook_2_time', 'twinspires_1_odds', 'twinspires_1_time', 'twinspires_2_odds', 'twinspires_2_time', 'unibet_1_odds', 'unibet_1_time', 'unibet_2_odds', 'unibet_2_time', 'unibet_eu_1_odds', 'unibet_eu_1_time', 'unibet_eu_2_odds', 'unibet_eu_2_time', 'unibet_uk_1_odds', 'unibet_uk_1_time', 'unibet_uk_2_odds', 'unibet_uk_2_time', 'unibet_us_1_odds', 'unibet_us_1_time', 'unibet_us_2_odds', 'unibet_us_2_time', 'williamhill_1_odds', 'williamhill_1_time', 'williamhill_2_odds', 'williamhill_2_time', 'williamhill_us_1_odds', 'williamhill_us_1_time', 'williamhill_us_2_odds', 'williamhill_us_2_time', 'wynnbet_1_odds', 'wynnbet_1_time', 'wynnbet_2_odds', 'wynnbet_2_time']

