import json
import operator
import time
from datetime import timedelta

import numpy as np
import pandas as pd
import requests
from numpy.ma.bench import timer

import barstool
import betonlineag
import mybookieag
import notification
import fanduel
from scripts import draftkings

user_sport = 'basketball_nba'

def run(bookmakers, accurate_bookmaker, bookmakers_available_list, params, check_list):
    # get the json of the odds with the sport and bookmakers we want to look at
    data = get_data(bookmakers)

    # parse the data and return
    results = parse_data(data, accurate_bookmaker, bookmakers_available_list, params, check_list)



def get_data(bookmakers):
    API_KEY = '6b7c5a1a854ea2d45d5d9d0f958dd3a0'

    SPORT = 'basketball_nba'

    MARKETS = 'h2h'  # h2h | spreads | totals. Multiple can be specified if comma delimited

    ODDS_FORMAT = 'american'

    DATE_FORMAT = 'iso'

    BOOKMAKERS = bookmakers

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


def make_df1(bookie, accurate_bookmaker):
    last_update = pd.to_datetime(bookie['last_update'], format='%Y-%m-%dT%H:%M:%SZ')

    df1 = pd.DataFrame(
        {'team': [bookie['markets'][0]['outcomes'][0]['name'],
                  bookie['markets'][0]['outcomes'][1]['name']],
         'moneyline': [bookie['markets'][0]['outcomes'][0]['price'],
                       bookie['markets'][0]['outcomes'][1]['price']],
         'last_update': [last_update, last_update],
         'bookie': [accurate_bookmaker, accurate_bookmaker]
         })

    return df1


def make_df2(bookie):
    last_update = pd.to_datetime(bookie['last_update'], format='%Y-%m-%dT%H:%M:%SZ')
    df2 = pd.DataFrame({'team': [bookie['markets'][0]['outcomes'][0]['name'],
                                 bookie['markets'][0]['outcomes'][1]['name']],
                        'moneyline': [bookie['markets'][0]['outcomes'][0]['price'],
                                      bookie['markets'][0]['outcomes'][1]['price']],
                        'last_update': [last_update, last_update],
                        'bookie': [bookie['key'], bookie['key']]
                        })

    return df2


def make_fair_odds_dict(bookie):
    # Calc the fair odds and store in dict
    fair_odds_dict = {
        bookie['markets'][0]['outcomes'][0]['name']: calc_fair_odds(
            bookie['markets'][0]['outcomes'][0]['price'], bookie['markets'][0]['outcomes'][1]['price']),
        bookie['markets'][0]['outcomes'][1]['name']: calc_fair_odds(
            bookie['markets'][0]['outcomes'][1]['price'], bookie['markets'][0]['outcomes'][0]['price'])
    }

    return fair_odds_dict


def parse_data(data, accurate_bookmaker, bookmakers, params, check_list):


    for game in data:
        accurate_bookmaker_first_team_odds = -1000000
        accurate_bookmaker_second_team_odds = -1000000
        found = False
        team_1_list = []
        team_2_list = []
        try:
            for bookie in game['bookmakers']:
                # We're now looking at the accurate bookmakers data
                if bookie['key'] == accurate_bookmaker and not found:
                    # Store the accurate bookmakers data in a df
                    df1 = make_df1(bookie, accurate_bookmaker)

                    accurate_bookmaker_last_update_mst = pd.to_datetime(bookie['last_update'], format='%Y-%m-%dT%H:%M:%SZ')-timedelta(hours=7)

                    accurate_bookmaker_first_team_odds = bookie['markets'][0]['outcomes'][0]['price']
                    accurate_bookmaker_second_team_odds = bookie['markets'][0]['outcomes'][1]['price']

                    # Calc the fair odds. This is a dict that looks like this: "team_name":"prob",
                    #                                                           "team_name":"prob"
                    fair_odds_dict = make_fair_odds_dict(bookie)

                    found = True
        except:
            print("Couldn't get accurate bookmaker odds for this game")
            return


        try:
            for bookie in game['bookmakers']:
                for bettable_book in bookmakers:
                    if bookie['key'] == bettable_book:
                        bad_bookmaker_last_update_mst = pd.to_datetime(bookie['last_update'],
                                                                       format='%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=7)

                        if compare_times(bad_bookmaker_last_update_mst, accurate_bookmaker_last_update_mst):

                            if bookie['markets'][0]['outcomes'][0]['price'] > accurate_bookmaker_first_team_odds or \
                                bookie['markets'][0]['outcomes'][1]['price'] > accurate_bookmaker_second_team_odds:
                                # Makes this info into a df for some reason tbd
                                df2 = make_df2(bookie)

                                 # Merge the DataFrames on the 'team' column
                                merged_df = pd.merge(df1, df2, on='team',
                                                     suffixes=(f"_{accurate_bookmaker}", f"_{bookie['key']}"))

                                merged_df.to_csv("/Users/stefanfeiler/Desktop/merged.csv", mode='a')

                                # Take the data for each game and make it into a list
                                values_list_1 = merged_df.iloc[0].tolist()
                                values_list_2 = merged_df.iloc[1].tolist()

                                team_1 = {
                                    'team': values_list_1[0],
                                    'bookie': values_list_1[6],
                                    'moneyline': values_list_1[4],
                                    'last_update': values_list_1[5],
                                    'ev': calc_ev(fair_odds_dict[values_list_1[0]], values_list_1[4], params),
                                    'live': False if values_list_1[5] <= pd.to_datetime(game['commence_time'],
                                                                                        format='%Y-%m-%dT%H:%M:%SZ') else True,
                                } if values_list_1[0] in fair_odds_dict else 0

                                team_2 = {
                                    'team': values_list_2[0],
                                    'bookie': values_list_2[6],
                                    'moneyline': values_list_2[4],
                                    'last_update': values_list_2[5],
                                    'ev': calc_ev(fair_odds_dict[values_list_2[0]], values_list_2[4], params),
                                    'live': False if values_list_2[5] <= pd.to_datetime(game['commence_time'],
                                                                                        format='%Y-%m-%dT%H:%M:%SZ') else True,
                                } if values_list_2[0] in fair_odds_dict else 0

                                team_1_list.append(team_1)

                                team_2_list.append(team_2)

            team_1_list_sorted = sorted(team_1_list, key=operator.itemgetter('ev'), reverse=True)
            team_2_list_sorted = sorted(team_2_list, key=operator.itemgetter('ev'), reverse=True)

            placed = False

            for team in team_1_list_sorted:
                if not placed and team['ev'] >= params["EV"] and team['team'] not in check_list and team[
                  'bookie'] != accurate_bookmaker and team['moneyline'] <= params['MAX ODDS'] and compare_times(
                  bad_bookmaker_last_update_mst, accurate_bookmaker_last_update_mst):

                    placed = try_to_place(team, params, check_list)

            placed = False
            for team in team_2_list_sorted:
                if not placed and team['ev'] >= params["EV"] and team['team'] not in check_list and team[
                  'bookie'] != accurate_bookmaker and team['moneyline'] <= params['MAX ODDS'] and compare_times(
                 bad_bookmaker_last_update_mst, accurate_bookmaker_last_update_mst):

                    placed = try_to_place(team, params, check_list)

        except:
            pass
    return 0


def try_to_place(team, params, check_list):
    if team['bookie'].upper() == 'BARSTOOL':
        try:
            if barstool.try_to_place(team, params['DRIVERS']['barstool'], params):
                notification.placed(team['bookie'],
                                   team['team'],
                                   team['moneyline'],
                                   int(team['ev']))
                check_list.append(team['team'])
                print(f"Placed {team['team']} at {team['moneyline']} on {team['bookie']}")
                return True
            else:
                print(f"Unable to place {team['team']} at {team['moneyline']} on {team['bookie']}")
                return False
        except:
            print(f"Error placing {team['team']} at {team['moneyline']} on {team['bookie']}")
            return False

    elif team['bookie'].upper() == 'MYBOOKIEAG':
        try:
            if mybookieag.try_to_place(team, params['DRIVERS']['mybookieag'], params):
                notification.placed(team['bookie'],
                                   team['team'],
                                   team['moneyline'],
                                   int(team['ev']))
                check_list.append(team['team'])
                print(f"Placed {team['team']} at {team['moneyline']} on {team['bookie']}")
                return True
            else:
                print(f"Unable to place {team['team']} at {team['moneyline']} on {team['bookie']}")
                return False
        except:
            print(f"Error placing {team['team']} at {team['moneyline']} on {team['bookie']}")
            return False

    elif team['bookie'].upper() == 'BETONLINEAG':
        try:
            if betonlineag.try_to_place(team, params['DRIVERS']['betonlineag'], params):
                notification.placed(team['bookie'],
                                    team['team'],
                                    team['moneyline'],
                                    int(team['ev']))
                check_list.append(team['team'])
                print(f"Placed {team['team']} at {team['moneyline']} on {team['bookie']}")
                return True
            else:
                #   betonlineag.get_site(params['DRIVERS']['betonlineag'])
                print(f"Unable to place {team['team']} at {team['moneyline']} on {team['bookie']}")
                return False
        except:
            # betonlineag.get_site(params['DRIVERS']['betonlineag'])
            print(f"Error placing {team['team']} at {team['moneyline']} on {team['bookie']}")
            return False

    elif team['bookie'].upper() == 'DRAFTKINGS':
        try:
            if draftkings.try_to_place(team, params['DRIVERS']['draftkings'], params):
                notification.placed(team['bookie'],
                                   team['team'],
                                   team['moneyline'],
                                   int(team['ev']))
                check_list.append(team['team'])
                print(f"Placed {team['team']} at {team['moneyline']} on {team['bookie']}")
                return True
            else:
                print(f"Unable to place {team['team']} at {team['moneyline']} on {team['bookie']}")
                return False
        except:
            print(f"Error placing {team['team']} at {team['moneyline']} on {team['bookie']}")
            return False


def calc_profit(num):
    if num > 0:
        return num
    else:
        return (100 / abs(num)) * 100


def compare_times(s1, s2):
    if abs((s1 - s2).total_seconds()) <= 10:
        return True
    else:
        return False


def calc_fair_odds(num1, num2):
    if num1 > 0 and num2 < 0:
        dividend = 100 / (100 + num1)
        divisor = ((abs(num2) / (abs(num2) + 100)) + dividend)
        return dividend / divisor

    elif num1 < 0 and num2 > 0:
        dividend = abs(num1) / (abs(num1) + 100)
        divisor = ((100 / (100 + num2)) + dividend)
        return dividend / divisor

    elif num1 > 0 and num2 > 0:
        dividend = 100 / (100 + num1)
        divisor = (dividend + (100 / 100 + num2))
        return dividend / divisor

    elif num1 < 0 and num2 < 0:
        dividend = abs(num1) / (abs(num1) + 100)
        divisor = (dividend + (abs(num2) / (abs(num2) + 100)))
        return dividend / divisor


def calc_ev(fair_win_prob, odds_taken, params):
    prof = calc_profit(odds_taken)
    return (fair_win_prob * prof) - ((1 - float(fair_win_prob)) * 100)


def get_b(num):
    if num > 0:
        num = (num / 100)
    else:
        num = (100 / num)
    return num
