import barstool, draftkings, betonlineag, notification

def run(params, ev_dict, check_list, live_games_list):

    for team_name, ev_values in ev_dict.items():
        bet = False
        for bookmaker_name, ev in ev_values.items():
            team = {
                'bookie': bookmaker_name,
                'team': team_name,
                'moneyline': params['ODDS DICT'][team_name][bookmaker_name],
                'is_live': check_if_live(team_name, live_games_list)
            }
            if ev >= params['MIN EV'] and not bet and team_name not in check_list and try_to_place(team, params, check_list):
                bet = True


def check_if_live(team, lis):
    if team in lis:
        return True
    else:
        return False
    

def try_to_place(team, params, check_list):
    if team['bookie'].upper() == 'BARSTOOL':
        try:
            if barstool.try_to_place(team, params['DRIVERS']['barstool'], params):
                
                print(f"Placed {team['team']} on {team['bookie']} @{team['moneyline']}")

                notification.placed(team)
                
                check_list.append(team['team'])
                                
                return True
            else:
                print(f"Placing functinon failed on {team['bookie']}")
                return False
        except:
            print(f"Error placing {team['team']} at {team['moneyline']} on {team['bookie']}")
            return False

    elif team['bookie'].upper() == 'MYBOOKIEAG':
        try:
            if mybookieag.try_to_place(team, params['DRIVERS']['mybookieag'], params):
                
                print(f"Placed {team['team']} on {team['bookie']} @{team['moneyline']}")
                
                notification.placed(team)
                
                check_list.append(team['team'])
                
                print(f"Placed {team['team']} at {team['moneyline']} on {team['bookie']}")
                
                return True
            else:
                print(f"Placing functinon failed on {team['bookie']}")
                return False
        except:
            print(f"Error placing {team['team']} at {team['moneyline']} on {team['bookie']}")
            return False

    elif team['bookie'].upper() == 'BETONLINEAG':
        try:
            if betonlineag.try_to_place(team, params['DRIVERS']['betonlineag'], params):
                
                print(f"Placed {team['team']} at {team['moneyline']} on {team['bookie']}")

                notification.placed(team)
                
                check_list.append(team['team'])
                
                return True
            else:
                #   betonlineag.get_site(params['DRIVERS']['betonlineag'])
                print(f"Placing functinon failed on {team['bookie']}, may not be live")
                return False
        except:
            # betonlineag.get_site(params['DRIVERS']['betonlineag'])
            print(f"Error placing {team['team']} at {team['moneyline']} on {team['bookie']}")
            return False

    elif team['bookie'].upper() == 'DRAFTKINGS':
        try:
            if draftkings.try_to_place(team, params['DRIVERS']['draftkings'], params):
                
                print(f"Placed {team['team']} at {team['moneyline']} on {team['bookie']}")
                
                notification.placed(team)
                
                check_list.append(team['team'])
                                
                return True
            else:
                print(f"Placing functinon failed on {team['bookie']}")
                return False
        except:
            print(f"Error placing {team['team']} at {team['moneyline']} on {team['bookie']}")
            return False