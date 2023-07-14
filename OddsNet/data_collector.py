import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import torch
import warnings
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

class data_collector():
    def __init__(self, from_stacked=True,  min_minutes_since_commence=-1000000, max_minutes_since_commence=2400, min_avg_odds=0, max_avg_odds = 10000, min_ev=10, max_ev=1000, min_best_odds = -1, max_best_odds = 1000, n_last_games_odds = 3, n_last_games_win_perc = 10, n_last_matchups_odds = 3, n_last_matchups_record = 20):
        
        self.min_minutes_since_commence = min_minutes_since_commence
        self.max_minutes_since_commence = max_minutes_since_commence
        self.min_avg_odds = min_avg_odds
        self.max_avg_odds = max_avg_odds
        self.min_best_odds = min_best_odds
        self.max_best_odds = max_best_odds
        self.min_ev = min_ev
        self.max_ev = max_ev
        self.n_last_games_odds = n_last_games_odds
        self.n_last_games_win_perc = n_last_games_win_perc
        self.n_last_matchups_odds = n_last_matchups_odds
        self.n_last_matchups_record = n_last_matchups_record
        self.encoders = {}
        self.equal_shapes = False
        self.unique_teams = None

        self.bettable_books = ['barstool', 'betfred', 'betmgm', 'betonlineag', 'betrivers', 'betway', 'bovada', 'circasports', 'draftkings', 'fanduel', 'foxbet', 'pointsbet', 'superbook', 'twinspires', 'williamhill', 'wynnbet']
    
        # TODO: Change this location once the data is reorganized
        if from_stacked:
            self.df = pd.read_parquet('/Users/stefanfeiler/Desktop/SmartBetter/SmartBetter/data/stacked_w_opponent.parquet')
        elif not from_stacked:
            self.df = pd.read_parquet('/Users/stefanfeiler/Desktop/SmartBetter/SmartBetter/data/mlb_raw_final_for_model.parquet')
            self.all_columns = self.df.columns
            self.columns = self.all_columns[5:]
            self.info_columns = ['game_id', 'commence_time', 'time_pulled', 'home_team', 'away_team', 'team_1', 'team_2']
            self.odds_columns = [x for x in self.columns if x.endswith('_odds')]
            self.time_columns = [x for x in self.columns if x.endswith('_time')]
            self.categorical_columns = ['day_of_week', 'away_team_league', 'home_team_league', 'day_night', 'park_id']
            self.numerical_columns = ['number_of_game_today', 'away_team_game_number', 'home_team_game_number',]
            self.collect_and_stack_data()
        

        print(f'Length of df: {len(self.df)}')
        self.filter_by_params()

        print(f'Length of df after filter: {len(self.df)}')

        self.add_more_feature_variables()

        self.format_for_nn()
    # TODO: Fuck with this
    def replace_missing_vals(self):
        for col in self.odds_columns:
            self.df[col] = self.df[col].replace(np.nan, 0)
            self.df[col] = self.df[col].astype('float64')
        for col in self.time_columns:
            self.df[col] = self.df[col].replace(np.nan, '1/1/1970 00:00:00')
            self.df[col] = pd.to_datetime(self.df[col])

    def make_snapshot_time(self):
        self.df['snapshot_time_taken'] = self.df[self.time_columns].apply(lambda x: max(x), axis=1)
        self.df['snapshot_time_taken'] = pd.to_datetime(self.df['snapshot_time_taken'])
        self.df['commence_time'] = pd.to_datetime(self.df['commence_time'])

    def make_minutes_since_commence(self):
        self.df['minutes_since_commence'] = (self.df['snapshot_time_taken'] - self.df['commence_time']).dt.total_seconds()/60

    def make_hour_of_start(self):
        self.df['hour_of_start'] = self.df['commence_time'].dt.hour

    def stack_games(self):
        # Select the first subset:
        cols_with_one = [col for col in self.df.columns if '_1' in col]
        cols_with_two = [col for col in self.df.columns if '_2' in col]
        extra_cols = ['game_id', 'commence_time', 'time_pulled', 'home_team', 'away_team', 'number_of_game_today', 'day_of_week', 'away_team_league', 'away_team_game_number', 'home_team_league', 'home_team_game_number', 'day_night', 'park_id', 'winning_team', 'minutes_since_commence', 'snapshot_time_taken', 'hour_of_start']

        for each in extra_cols:
            cols_with_one.append(each)
            cols_with_two.append(each)

        df1 = self.df[cols_with_one]
        df2 = self.df[cols_with_two]

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

        df_stacked['target'] = np.where(df_stacked['team_1'] == df_stacked['winning_team'], 1, 0)

        df_stacked['opponent'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], df_stacked['away_team'], df_stacked['home_team'])

        df_stacked['this_team_league'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], df_stacked['home_team_league'], df_stacked['away_team_league'])

        df_stacked['opponent_league'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], df_stacked['away_team_league'], df_stacked['home_team_league'])

        df_stacked['this_team_game_of_season'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], df_stacked['home_team_game_number'], df_stacked['away_team_game_number'])

        df_stacked['opponent_game_of_season'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], df_stacked['away_team_game_number'], df_stacked['home_team_game_number'])

        df_stacked['home_away'] = np.where(df_stacked['team_1'] == df_stacked['home_team'], 1, 0)

        df_stacked['snapshot_time'] = df_stacked['snapshot_time_taken'].dt.time

        cols_to_drop=['commence_time', 'time_pulled', 'home_team', 'away_team', 'away_team_league', 'away_team_game_number','home_team_league', 'home_team_game_number', 'winning_team', 'snapshot_time_taken']

        result = df_stacked.drop(columns=cols_to_drop)

        self.df = result
        
    def collect_and_stack_data(self):
        self.replace_missing_vals()
        self.make_snapshot_time()
        self.make_minutes_since_commence()
        self.make_hour_of_start()
        self.stack_games()
    
    def add_more_feature_variables(self):
       # self.make_average_market_odds()
        self.make_game_avg_odds()
        self.make_avg_odds_n_last_games(self.n_last_games_odds)
        self.make_record_last_n_games(self.n_last_games_win_perc)
        self.make_avg_odds_n_last_matchups(self.n_last_matchups_odds)
        self.make_record_n_last_matchups(self.n_last_matchups_record)
        self.make_winner_of_last_matchup()

        self.df = self.df.drop('opponent', axis=1)
        self.df = self.df.drop('game_id_plus_team', axis=1)

    def make_average_market_odds(self):
        odds_columns = [x for x in self.df.columns if x.endswith('_odds')]
        odds_df = self.df[odds_columns]
        df_array = odds_df.values
        # Create mask for values greater than 0.5
        mask = df_array > 0.5

        # Apply mask and calculate row-wise average
        row_avg = np.nanmean(np.where(mask, df_array, np.nan), axis=1)

        self.df['average_market_odds'] = row_avg

    def make_game_avg_odds(self):

        self.df['game_avg_odds'] = np.nan  # Use np.nan to represent missing values

        self.unique_teams = self.df['team_1'].unique()

        self.df['game_avg_odds'] = self.df.groupby(['game_id', 'team_1'])['average_market_odds'].transform('mean')

        self.df['game_id_plus_team'] = self.df['game_id'] + self.df['team_1']

    def make_avg_odds_n_last_games(self,n):
        my_dict = {}

        for team in self.unique_teams:
            team_df = self.df[self.df['team_1'] == team]
            subset_df = team_df.drop_duplicates(subset='game_id')
            for i in range(n):
                subset_df[f'prev_game_{i+1}'] = subset_df['game_avg_odds'].shift(-(i+1))
            for index, row in subset_df.iterrows():
                my_list = []
                for i in range(n):
                    val = row[f'prev_game_{i+1}']
                    if not np.isnan(val):
                        my_list.append(val)
                my_dict[row['game_id_plus_team']] = my_list

        for key in my_dict:
            value_list = my_dict[key]
            if len(value_list) > 0:
                average_value  = np.mean(value_list)
                my_dict[key] = average_value
            else:
                my_dict[key] = 2

        self.df['last_n_avg_game_odds'] = self.df['game_id_plus_team'].map(my_dict)

    def make_record_last_n_games(self, n):
        my_dict = {}
        for team in self.unique_teams:
            team_df = self.df[self.df['team_1'] == team]
            subset_df = team_df.drop_duplicates(subset='game_id')

            for i in range(n):
                subset_df[f'prev_game_{i+1}'] = subset_df['target'].shift(-(i+1))

            for index, row in subset_df.iterrows():
                my_list = []
                for i in range(n):
                    val = row[f'prev_game_{i+1}']
                    if not np.isnan(val):
                        my_list.append(val)
                    
                my_dict[row['game_id_plus_team']] = my_list

        for key in my_dict:
            value_list = my_dict[key]
            if len(value_list) > 0:
                average_value  = np.mean(value_list)
                my_dict[key] = average_value
            else:
                my_dict[key] = 0

        self.df['last_n_win_perc'] = self.df['game_id_plus_team'].map(my_dict)

    def make_avg_odds_n_last_matchups(self, n):
        my_dict = {game_id: list(group['team_1'].unique()) for game_id, group in self.df.groupby('game_id')}

        my_new_dict = {}

        for team in self.unique_teams:
        
            team_df = self.df[self.df['team_1'] == team]

            subset_df = team_df.drop_duplicates(subset='game_id')

            unique_opponents = team_df['opponent'].unique()

            for opponent in unique_opponents:
                matchups_df = subset_df[subset_df['opponent'] == opponent]
        
                for i in range(n):
                    matchups_df[f'prev_matchup_{i+1}'] = matchups_df['game_avg_odds'].shift(-(i+1))

                for index, row in matchups_df.iterrows():
                    my_list = []
                    for i in range(n):
                        val = row[f'prev_matchup_{i+1}']

                        if not np.isnan(val):
                            my_list.append(val)
                
                    my_new_dict[row['game_id_plus_team']] = my_list

            my_dict = {key: value if type(value) is list else [value] for key, value in my_new_dict.items()}
            map_dict = {}
            for key, value_list in my_dict.items():
                if len(value_list) > 0:
                    average_value  = np.mean(value_list).item()
                    map_dict[key] = average_value
                else:
                    map_dict[key] = 2

            self.df['last_n_matchup_avg_odds'] = self.df['game_id_plus_team'].map(map_dict)

    def make_record_n_last_matchups(self, n):
        my_dict = {game_id: list(group['team_1'].unique()) for game_id, group in self.df.groupby('game_id')}

        my_new_dict = {}

        for team in self.unique_teams:
        
            team_df = self.df[self.df['team_1'] == team]

            subset_df = team_df.drop_duplicates(subset='game_id')

            unique_opponents = team_df['opponent'].unique()

            for opponent in unique_opponents:
                matchups_df = subset_df[subset_df['opponent'] == opponent]
        
                for i in range(n):
                    matchups_df[f'prev_matchup_{i+1}'] = matchups_df['target'].shift(-(i+1))

                for index, row in matchups_df.iterrows():
                    my_list = []
                    for i in range(n):
                        val = row[f'prev_matchup_{i+1}']

                        if not np.isnan(val):
                            my_list.append(val)
                
                    my_new_dict[row['game_id_plus_team']] = my_list

            my_dict = {key: value if type(value) is list else [value] for key, value in my_new_dict.items()}
            map_dict = {}
            for key, value_list in my_dict.items():
                if len(value_list) > 0:
                    average_value  = np.mean(value_list).item()
                    map_dict[key] = average_value
                else:
                    map_dict[key] = 2

            self.df['last_n_matchup_record'] = self.df['game_id_plus_team'].map(map_dict)

    def make_winner_of_last_matchup(self):
        n = 1
        my_dict = {game_id: list(group['team_1'].unique()) for game_id, group in self.df.groupby('game_id')}

        my_new_dict = {}

        for team in self.unique_teams:
        
            team_df = self.df[self.df['team_1'] == team]

            subset_df = team_df.drop_duplicates(subset='game_id')

            unique_opponents = team_df['opponent'].unique()

            for opponent in unique_opponents:
                matchups_df = subset_df[subset_df['opponent'] == opponent]
        
                for i in range(n):
                    matchups_df[f'prev_matchup_{i+1}'] = matchups_df['target'].shift(-(i+1))

                for index, row in matchups_df.iterrows():
                    my_list = []
                    for i in range(n):
                        val = row[f'prev_matchup_{i+1}']

                        if not np.isnan(val):
                            my_list.append(val)
                
                    my_new_dict[row['game_id_plus_team']] = my_list

            my_dict = {key: value if type(value) is list else [value] for key, value in my_new_dict.items()}
            map_dict = {}
            for key, value_list in my_dict.items():
                if len(value_list) > 0:
                    average_value  = np.mean(value_list).item()
                    map_dict[key] = average_value
                else:
                    map_dict[key] = 2

            self.df['winner_last_game'] = self.df['game_id_plus_team'].map(map_dict)

    def filter_by_minutes_since_commence(self):
        self.df = self.df[self.df['minutes_since_commence'] >= self.min_minutes_since_commence]
        self.df = self.df[self.df['minutes_since_commence'] <= self.max_minutes_since_commence]

    def filter_by_average_market_odds(self):
        self.df = self.df[self.df['average_market_odds'] >= self.min_avg_odds]
        self.df = self.df[self.df['average_market_odds'] <= self.max_avg_odds]
    
    def filter_by_ev_thresh(self):
        self.odds_columns = [x for x in self.df.columns if x.endswith('_odds')]

        subset_columns = [col for col in self.odds_columns if any(item in col for item in self.bettable_books)]

        self.df['highest_bettable_odds'] = self.df[subset_columns].max(axis=1)
        #self.df['highest_bettable_book'] = self.df[subset_columns].apply(lambda row: row.idxmax().split('_')[0], axis=1)

        self.df['ev'] = ((1/self.df['average_market_odds'])*(100*self.df['highest_bettable_odds']-100)) - ((1-(1/self.df['average_market_odds'])) * 100)

        self.df = self.df[self.df['ev'] >= self.min_ev]
        self.df = self.df[self.df['ev'] <= self.max_ev]

        #self.df.drop('highest_bettable_odds', axis='columns')
        #self.df.drop('highest_bettable_book', axis='columns')
        self.df.drop('ev', axis='columns')

    def filter_by_best_odds(self):
        self.df = self.df[self.df['highest_bettable_odds'] >= self.min_best_odds]
        self.df = self.df[self.df['highest_bettable_odds'] <= self.max_best_odds]

    def filter_by_params(self):
        self.make_average_market_odds()
        self.filter_by_minutes_since_commence()
        self.filter_by_average_market_odds()
        self.filter_by_ev_thresh()
        self.filter_by_best_odds()

    def replace_bad_vals_for_split(self):
        self.df.loc[self.df['park_id'] == 'WIL02', 'park_id'] = 'LOS03'
        self.df.loc[self.df['park_id'] == 'DYE01', 'park_id'] = 'LOS03'
        # self.df.loc[self.df['park_id'] == 'BUF05', 'park_id'] = 'LOS03'
        # self.df.loc[self.df['park_id'] == 'DUN01', 'park_id'] = 'LOS03'

        self.df.loc[self.df['hour_of_start'] == 20, 'hour_of_start'] = 19
        self.df.loc[self.df['hour_of_start'] == 8, 'hour_of_start'] = 9

        # Group by 'park_id' and count the number of unique 'game_id' values
        # park_id_game_count = self.df.groupby('hour_of_start')['game_id'].nunique().reset_index()
        # sorted_counts = park_id_game_count.sort_values('game_id')
        # print(sorted_counts)
        # park_id_game_count = self.df.groupby('park_id')['game_id'].nunique().reset_index()
        # sorted_counts = park_id_game_count.sort_values('game_id')
        # print(sorted_counts)
        # park_id_game_count = self.df.groupby('team_1')['game_id'].nunique().reset_index()
        # sorted_counts = park_id_game_count.sort_values('game_id')
        # print(sorted_counts)
        
    def add_category(self, column_name, data):
      
      arr = data[column_name].values.reshape(-1,1)
      
      coder = OneHotEncoder(sparse_output=False)
      
      onehots = coder.fit_transform(arr)
      
      self.encoders[column_name] = coder

      print(onehots.shape)
      
      return onehots

    def add_numeric(self, column_name, data):
      # Make an array of the column values 
      arr = data[column_name].values.reshape(-1,1).astype('float')
      
      return arr

    def add_all_numeric_and_categorical(self, input_df):
      data = input_df
      return_data = np.concatenate(
          [
              self.add_numeric('barstool_1_odds', data),
              self.add_numeric('betclic_1_odds', data),
              self.add_numeric('betfair_1_odds', data),
              self.add_numeric('betfred_1_odds', data),
              self.add_numeric('betmgm_1_odds', data),
              self.add_numeric('betonlineag_1_odds', data),
              self.add_numeric('betrivers_1_odds', data),
              self.add_numeric('betus_1_odds', data),
              self.add_numeric('betway_1_odds', data),
              self.add_numeric('bovada_1_odds', data),
              self.add_numeric('casumo_1_odds', data),
              self.add_numeric('circasports_1_odds', data),
              self.add_numeric('coral_1_odds', data),
              self.add_numeric('draftkings_1_odds', data),
              self.add_numeric('fanduel_1_odds', data),
              self.add_numeric('foxbet_1_odds', data),
              self.add_numeric('gtbets_1_odds', data),
              self.add_numeric('ladbrokes_1_odds', data),
              self.add_numeric('lowvig_1_odds', data),
              self.add_numeric('marathonbet_1_odds', data),
              self.add_numeric('matchbook_1_odds', data),
              self.add_numeric('mrgreen_1_odds', data),
              self.add_numeric('mybookieag_1_odds', data),
              self.add_numeric('nordicbet_1_odds', data),
              self.add_numeric('onexbet_1_odds', data),
              self.add_numeric('paddypower_1_odds', data),
              self.add_numeric('pinnacle_1_odds', data),
              self.add_numeric('pointsbetus_1_odds', data),
              self.add_numeric('sport888_1_odds', data),
              self.add_numeric('sugarhouse_1_odds', data),
              self.add_numeric('superbook_1_odds', data),
              self.add_numeric('twinspires_1_odds', data),
              self.add_numeric('unibet_1_odds', data),
              self.add_numeric('unibet_eu_1_odds', data),
              self.add_numeric('unibet_uk_1_odds', data),
              self.add_numeric('unibet_us_1_odds', data),
              self.add_numeric('williamhill_1_odds', data),
              self.add_numeric('williamhill_us_1_odds', data),
              self.add_numeric('wynnbet_1_odds', data),
              self.add_numeric('highest_bettable_odds', data),
              self.add_numeric('minutes_since_commence', data),
              self.add_numeric('this_team_game_of_season', data),
              self.add_numeric('opponent_game_of_season', data),
              self.add_numeric('average_market_odds', data),
              self.add_numeric('ev', data),
              self.add_numeric('last_n_avg_game_odds', data),
              self.add_numeric('last_n_win_perc', data),
              self.add_numeric('last_n_matchup_avg_odds', data),
              self.add_numeric('last_n_matchup_record', data),
              self.add_numeric('winner_last_game', data),
              
              self.add_category('home_away', data),
              self.add_category('team_1', data),
              self.add_category('hour_of_start', data),
              self.add_category('day_of_week', data),
              self.add_category('number_of_game_today', data),
              self.add_category('day_night', data),
              self.add_category('park_id', data),
              self.add_category('this_team_league', data),
              self.add_category('opponent_league', data),
          ],
          1
      )

      return return_data

    def make_train_test_val_splits(self):

        categorical_vars = ['park_id', 'team_1', 'hour_of_start']

       # Assuming you have a DataFrame called 'df' and a list of categorical variables 'categorical_vars'
        class_counts = self.df.groupby(categorical_vars).size().reset_index(name='count')

        # Find the class combinations with only one member
        single_member_classes = class_counts[class_counts['count'] == 1]

        # Create a mask for rows to be removed
        mask = self.df[categorical_vars].apply(tuple, axis=1).isin(single_member_classes[categorical_vars].apply(tuple, axis=1))

        # Get the indices of rows to be removed
        indices_to_remove = self.df[mask].index

        # Delete the rows from the DataFrame
        self.df = self.df.drop(indices_to_remove, axis=0).reset_index(drop=True)
        # Assuming you have a DataFrame called 'df' and the game ID column is named 'game_id'
        game_ids = self.df['game_id'].unique()

        # Split the game IDs into training, validation, and testing sets
        train_game_ids, remaining_game_ids = train_test_split(game_ids, test_size=0.3, random_state=42)
        val_game_ids, test_game_ids = train_test_split(remaining_game_ids, test_size=0.5, random_state=42)

        # Split the original DataFrame based on the selected game IDs
        self.training_data = self.df[self.df['game_id'].isin(train_game_ids)]
        self.validation_data = self.df[self.df['game_id'].isin(val_game_ids)]
        self.testing_data = self.df[self.df['game_id'].isin(test_game_ids)]

        train_game_ids = set(self.training_data['game_id'].unique())
        val_game_ids = set(self.validation_data['game_id'].unique())
        test_game_ids = set(self.testing_data['game_id'].unique())

        if set(train_game_ids) & set(val_game_ids):
            print("The lists have shared values.")
        elif set(train_game_ids) & set(test_game_ids):
            print("Overlap")
        elif set(test_game_ids) & set(val_game_ids):
            print("overlap")
        else:
            print("The lists do not have shared values.")


        self.full_y = self.df['target']
        self.full_data = self.df.drop('target', axis='columns')

        self.training_y = self.training_data['target']
        self.training_data = self.training_data.drop('target', axis='columns')

        self.testing_y = self.testing_data['target']
        self.testing_data = self.testing_data.drop('target', axis='columns')

        self.validation_y = self.validation_data['target']
        self.validation_data = self.validation_data.drop('target', axis = 'columns')

        self.full_data = self.add_all_numeric_and_categorical(self.df)
        self.training_data = self.add_all_numeric_and_categorical(self.training_data)
        self.testing_data = self.add_all_numeric_and_categorical(self.testing_data)
        self.validation_data = self.add_all_numeric_and_categorical(self.validation_data)

    def standardize_numerical(self):
        # Define the indices of the columns you want to standardize and those we don't
        continuous_vars = self.full_data[:, :49]
        categorical_vars = self.full_data[:, 49:]

        # Create an instance of StandardScaler and fit it on the training data
        scaler = StandardScaler()
        scaler.fit(continuous_vars)
        self.scaler = scaler

        continuous_vars_train = self.training_data[:, :49]
        categorical_vars_train = self.training_data[:, 49:]

        continuous_vars_test = self.testing_data[:, :49]
        categorical_vars_test = self.testing_data[:, 49:]

        continuous_vars_val = self.validation_data[:, :49]
        categorical_vars_val = self.validation_data[:, 49:]

        continuous_vars_full = self.full_data[:, :49]
        categorical_vars_full = self.full_data[:, 49:]

        # Standardize the columns of the dataset
        self.X_train = np.hstack((scaler.transform(continuous_vars_train), categorical_vars_train))
        self.X_test = np.hstack((scaler.transform(continuous_vars_test), categorical_vars_test))
        self.X_val = np.hstack((scaler.transform(continuous_vars_val), categorical_vars_val))
        self.X_full = np.hstack((scaler.transform(continuous_vars_full), categorical_vars_full))

    def make_data_loaders(self):
        # Convert input data to numpy arrays
        X_train_np = self.X_train.astype(np.float32)
        X_test_np = self.X_test.astype(np.float32)
        X_val_np = self.X_val.astype(np.float32)

        y_train_np = self.training_y.values.astype(np.float32)  # Convert y_train to numpy array
        y_test_np = self.testing_y.values.astype(np.float32)    # Convert y_test to numpy array
        y_val_np = self.validation_y.values.astype(np.float32)

        # Create Torch datasets with the numpy arrays
        self.train_data = torch.utils.data.TensorDataset(torch.tensor(X_train_np), torch.tensor(y_train_np))
        self.test_data = torch.utils.data.TensorDataset(torch.tensor(X_test_np), torch.tensor(y_test_np))
        self.val_data = torch.utils.data.TensorDataset(torch.tensor(X_val_np), torch.tensor(y_val_np))

    def check_dataset_sizes(self):

        if self.full_data.shape[1] == self.testing_data.shape[1] == self.validation_data.shape[1] == self.training_data.shape[1]:
            self.equal_shapes = True
        else:
            print(self.full_data.shape[1])
            print(self.testing_data.shape[1])
            print(self.validation_data.shape[1])
            print(self.training_data.shape[1])
            print('-----------------')
            self.equal_shapes = False

    def format_for_nn(self):
        self.replace_bad_vals_for_split()
        
        while not self.equal_shapes:

            self.make_train_test_val_splits()

            self.check_dataset_sizes()

        self.standardize_numerical()

        self.make_data_loaders()