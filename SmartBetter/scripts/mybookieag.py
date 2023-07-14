import time
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


def open_browser():
    driver = webdriver.Chrome(
        executable_path="//drivers/mybookieag")
    driver.maximize_window()
    driver.get("https://www.mybookie.ag/sportsbook")
    login_func(driver)
    login_input = input("Are you logged in to Mybookieag?")

    if login_input.upper() == "YES":
        find_nba(driver)
        return driver


def try_to_place(team, driver, params):
    # First check if there's a bet from the last round that wasn't removed, clear the betslip and start full from scratch if so

    team_to_bet = team['team']
    moneyline_target = team['moneyline']
    unit_size = params['STAKE']
    is_live = team['live']

    print(f"{team['bookie']} {team_to_bet} @{moneyline_target}, ${unit_size}, {is_live}")

    # find_sport(driver, "NBA")

    return get_moneyline_box(team_to_bet, moneyline_target, driver, params)


def get_moneyline_box(team_to_bet, moneyline_target, driver, params):
    team = team_to_bet.split(' ')[-1]

    teams = driver.find_elements('xpath', '//span[contains(@class,"team-name")]')
    found = False
    for span in teams:
        if team in span.get_attribute("textContent") and not found:
            game = span
            found = True

    # find the first ancestor div element that contains the class "game-line px-2"
    gp = game.find_element(By.XPATH, "ancestor::div[@class='game-line px-2']")

    spans = gp.find_elements(By.XPATH, ".//span[contains(@class, 'team-name')]")

    moneylines = gp.find_elements(By.XPATH, ".//button[@data-wager-type='ml']")

    i = 0
    for i, span in enumerate(spans):
        if team in span.get_attribute("textContent"):
            i = i
            break
    else:
        return False

    moneylines[i].click()

    bet_slip = WebDriverWait(driver, 5).until(
        (EC.presence_of_element_located((By.XPATH, "//a[@id='bet-slip-tab']"))))

    time.sleep(1)
    bet_slip.click()

    accept_all_odds_changes = WebDriverWait(driver, 5).until(
        (EC.presence_of_element_located((By.XPATH, "//div[contains(text(), ' Accept All Odds Changes ')]//span[1]"))))


    accept_all_odds_changes.click()

    site_ml = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//span[@class='bet-content__selection__info__odds']"))
    )

    site_ml = site_ml.get_attribute("textContent")


    try:
        if check_odds(moneyline_target, site_ml):
            worked = make_bet(driver, params)
            return worked
        else:
            remove_bets(driver)
    except:
        remove_bets(driver)
        return False

    return False


def make_bet(driver, params):

    try:
        wager_box = WebDriverWait(driver, 5).until(
            (EC.presence_of_element_located((By.XPATH, "//input[@name='risk_straight']"))))
        wager_box.send_keys(params["STAKE"])
        try:
            button = WebDriverWait(driver, 2).until(
                (EC.presence_of_element_located((By.XPATH, "//button[@id='bs-place-bet']"))))
            button.click()
        except:
            remove_bets(driver)

        button = WebDriverWait(driver, 6).until(
            (EC.presence_of_element_located((By.XPATH, "//button[contains(@id, 'start_new_bet')]"))))
        button.click()

        return True

    except:
        remove_bets(driver)
        return False


def check_odds(moneyline_target, site_ml):

    if site_ml[1] == "+":
        site_ml = int(site_ml[1:])
    elif site_ml[1] == "-":
        site_ml = int(site_ml[1:]) * -1

    if site_ml >= moneyline_target:
        return True

    elif abs(site_ml - moneyline_target) <= 5:
        return True

    else:
        return False


def login_func(driver):
    login_button = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "login-btn-box__login"))
    )

    login_button.click()

    email_field = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.NAME, "username"))
    )

    email_field.send_keys("feilerbets@gmail.com")

    pass_field = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.NAME, "password"))
    )

    pass_field.send_keys("Lacrosse32$")

    login_final = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "login_trk"))
    )

    login_final.click()

    return


def remove_bets(driver):
    selected_div = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@class='clear_bet_slip']"))
    )

    selected_div.click()


def find_nba(driver):
    selected_div = driver.find_element('xpath', "//a[@data-type='featured'][contains(text(), 'NBA')]")
    selected_div.click()


def refresh(driver):
    driver.get("https://www.mybookie.ag/sportsbook")

    NBA = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@data-type='featured'][contains(text(), 'NBA')]"))
    )

    NBA.click()

    return
