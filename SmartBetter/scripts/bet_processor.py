from bots import barstool, mybookieag, draftkings, betonlineag
from scripts import notification


def process(ev_dict, odds_dict, params, check_list):
    accurate_bookmaker = "draftkings"
    for team, bookmakers in ev_dict.items():
        placed = False
        for bookmaker, value in bookmakers.items():
            if not placed and accurate_bookmaker not in bookmaker and team not in check_list:

                moneyline_target = odds_dict[team][bookmaker]

                #ev_target = odds_dict[team][bookmaker]??

                placed = try_to_place(team, bookmaker, moneyline_target, params, check_list)


#TODO: FIND THE EV VALUE AND PASS IT
def try_to_place(team, bookmaker, moneyline_target, params, check_list):
    if bookmaker.upper() == 'BARSTOOL':
        try:
            if barstool.try_to_place(team, moneyline_target, params['DRIVERS']['barstool'], params):
                notification.placed(bookmaker,
                                    team,
                                    moneyline_target,
                                    10,
                                    #int(team['ev']
                                    #
                                    )
                check_list.append(team)
                print(f"Placed {team} at {moneyline_target} on {bookmaker}")
                return True
            else:
                print(f"Unable to place {team} at {moneyline_target} on {bookmaker}")
                return False
        except:
            print(f"Error placing {team} at {moneyline_target} on {bookmaker}")
            return False

    elif bookmaker.upper() == 'MYBOOKIEAG':
        try:
            if mybookieag.try_to_place(team, params['DRIVERS']['mybookieag'], params):
                # notification.placed(team['bookie'],
                #                   team['team'],
                #                  team['moneyline'],
                #                 int(team['ev']))
                check_list.append(team['team'])
                print(f"Placed {team['team']} at {team['moneyline']} on {team['bookie']}")
                return True
            else:
                print(f"Unable to place {team['team']} at {team['moneyline']} on {team['bookie']}")
                return False
        except:
            print(f"Error placing {team['team']} at {team['moneyline']} on {team['bookie']}")
            return False

    elif bookmaker.upper() == 'BETONLINEAG':
        try:
            if betonlineag.try_to_place(team, moneyline_target, params['DRIVERS']['betonlineag'], params):
                notification.placed(bookmaker,
                                    team,
                                    moneyline_target,
                                    10,
                                    #int(team['ev'])
                                    )
                check_list.append(team)
                print(f"Placed {team} at {moneyline_target} on {bookmaker}")
                return True
            else:
                #   betonlineag.get_site(params['DRIVERS']['betonlineag'])
                print(f"Unable to place {team} at {moneyline_target} on {bookmaker}")
                return False
        except:
            # betonlineag.get_site(params['DRIVERS']['betonlineag'])
            print(f"Error placing {team} at {moneyline_target} on {bookmaker}")

            return False

    elif bookmaker.upper() == 'DRAFTKINGS':
        try:
            if draftkings.try_to_place(team, moneyline_target, params['DRIVERS']['draftkings'], params):
                notification.placed(bookmaker,
                                    team,
                                    moneyline_target,
                                    10
                                    )
                                #int(team['ev'])
                check_list.append(team)
                print(f"Placed {team} at {moneyline_target} on {bookmaker}")
                return True
            else:
                print(f"Unable to place {team} at {moneyline_target} on {bookmaker}")
                return False
        except:
            print(f"Error placing {team} at {moneyline_target} on {bookmaker}")

            return False
