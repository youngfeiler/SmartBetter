import copy
import time
import requests
import pandas as pd
from datetime import datetime, timedelta

class live_odds_getter():
    
    def __init__(self, ):
        self.API_KEY = '6b7c5a1a854ea2d45d5d9d0f958dd3a0'
        self.SPORT = 'basketball_nba'

        self.MARKETS = 'h2h'

        self.ODDS_FORMAT = 'american'

        self.DATE_FORMAT = 'iso'

        # TODO: Update this to contain all the bookmakers that we want to use in our model
        self.BOOKMAKERS = "draftkings"


    def get_market_data(self):

      odds_response = requests.get(
          f'https://api.the-odds-api.com/v4/sports/{self.SPORT}/odds/',
          params={
              'api_key': self.API_KEY,
              'markets': self.MARKETS,
              'oddsFormat': self.ODDS_FORMAT,
              'dateFormat': self.DATE_FORMAT,
              'bookmakers': self.BOOKMAKERS
          }
      )

      if odds_response.status_code != 200:
        print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')
        self.data = None
      else:
          odds_json = odds_response.json()

          self.data = odds_json

      
    def get_list_of_games(self) -> list:

      games = None

      def check_if_bettable(t) -> bool:

        dif = (datetime.now() - t).total_seconds()

        if dif >= 0 or -10800 <= dif:
            return True
        else:
            return False
          
      if self.data:
        games = []
        for game in self.data:
            
            commence_time_mst = pd.to_datetime(game['commence_time'], format='%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=7)

            try:
                for bookie in game['bookmakers']:
      
                    if bookie['key'].upper() == "draftkings".upper() and check_if_bettable(commence_time_mst):
                        
                        games.append(game['home_team'])

                        games.append(game['away_team'])

            except:
                print("Couldn't figure out if this game is within our timing parameters or not...")

      self.games = games
    

def run(data, scraped_odds_dict, params):

    accurate_bookmaker = "draftkings"

    intermediate1 = parse_data(data, accurate_bookmaker, scraped_odds_dict)

    intermediate = clean_dict(intermediate1, accurate_bookmaker)

    ev_dict, odds_dict = make_ev(intermediate, accurate_bookmaker)

    final = sort_dict(params['EV'], ev_dict)

    return final, odds_dict


def sort_dict(threshold, odds_dict):
    filtered_odds_dict = {
        team: {bookmaker: ev for bookmaker, ev in sub_dict.items() if ev is not None and ev > threshold} for
        team, sub_dict in odds_dict.items()}
    filtered_odds_dict = {team: ev for team, ev in filtered_odds_dict.items() if ev}

    for team in filtered_odds_dict:
        filtered_odds_dict[team] = {k: v for k, v in sorted(filtered_odds_dict[team].items(), key=lambda x: -x[1])}

    # print the filtered and sorted data
    return filtered_odds_dict


def make_ev(md, ab):
    md_copy = copy.deepcopy(md)

    for team, inner_dict in md.items():

        fair_prob = inner_dict.get(f'{ab} fair prob')

        for key, value in inner_dict.items():

            if 'fair prob' not in key and type(value) != type(None) and type(fair_prob) != type(None) and value != 0:
                new_val = calc_ev(float(fair_prob), value)

                inner_dict[key] = new_val

    return md, md_copy
    

def get_fair_odds(dict):
    merged_dict = []

    for d in dict:
        merged_dict.extend(d['data'])

    results = {}
    for item in merged_dict:
        id = item['id']
        if id not in results:
            results[id] = {}
        for odds in item['odds']:
            if odds['sports_book_name'] == "draftkings":
                results[id][item['home_team']] = odds[0]['price']
                results[id][item['away_team']] = odds[1]['price']


def calc_profit(num):
    if num > 0:
        return num
    else:
        return (100 / abs(num)) * 100


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


def calc_ev(fair_win_prob, odds_taken):
    prof = calc_profit(odds_taken)

    return float((fair_win_prob * prof) - ((1 - fair_win_prob) * 100))


def parse_data(data, accurate_bookmaker, scraped_odds_dict):
    fair_odds_dict = {}
    for game in data:
        try:
            for bookie in game['bookmakers']:
                # We're now looking at the accurate bookmakers data
                if bookie['key'].upper() == accurate_bookmaker.upper() and abs((pd.to_datetime(bookie['last_update'],
                                                                                                format='%Y-%m-%dT%H:%M:%SZ') - timedelta(
                        hours=7) - datetime.now()).total_seconds()) <= 5:
                    # Calc the fair odds. This is a dict that looks like this: "team_name":"prob",
                    #                                                           "team_name":"prob"
                    fair_odds_dict.update(make_fair_odds_dict(bookie))

        except:
            print("Couldn't get accurate bookmaker odds for this game")
            return
    for team in scraped_odds_dict:
        fair_prob = fair_odds_dict.get(team)
        scraped_odds_dict[team][f"{accurate_bookmaker} fair prob"] = fair_prob

    for team in scraped_odds_dict:
        for sub_key, sub_value in scraped_odds_dict[team].items():
            if 'fair prob' not in sub_key and not isinstance(sub_value, int):
                if sub_value.startswith("+") or sub_value.startswith("-") or sub_value.startswith("−"):
                    sub_value = sub_value.replace('−', '-')
                    scraped_odds_dict[team][sub_key] = int(float(sub_value))

    return scraped_odds_dict


def clean_dict(my_dict, accurate_bookmaker):
    for team in list(my_dict.keys()):
        if my_dict[team][f'{accurate_bookmaker} fair prob'] is None:
            del my_dict[team]
    return my_dict


def make_fair_odds_dict(bookie):
    # Calc the fair odds and store in dict
    fair_odds_dict = {
        bookie['markets'][0]['outcomes'][0]['name'].split(" ")[-1]: calc_fair_odds(
            bookie['markets'][0]['outcomes'][0]['price'], bookie['markets'][0]['outcomes'][1]['price']),
        bookie['markets'][0]['outcomes'][1]['name'].split(" ")[-1]: calc_fair_odds(
            bookie['markets'][0]['outcomes'][1]['price'], bookie['markets'][0]['outcomes'][0]['price'])
    }

    return fair_odds_dict
