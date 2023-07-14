def pull_market_odds():
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
          'dateFormat': DATE_FORMAT
      }
  )

  if odds_response.status_code != 200:
      print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')

  else:
      odds_json = odds_response.json()

      print(odds_json)

      return odds_json
