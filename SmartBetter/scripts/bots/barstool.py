import time
import base64

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# create a custom profile
from scripts import notification

options = webdriver.ChromeOptions()

from selenium import webdriver

# configure the profile to store cookies and cache
options.add_argument("--use-fake-ui-for-media-stream")
options.add_argument("--use-fake-device-for-media-stream")
options.add_argument("--disable-extensions")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-popup-blocking")
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-web-security")
options.add_argument("--disable-notifications")
options.add_argument("--enable-automation")
options.add_argument("--disable-background-timer-throttling")
options.add_argument("--disable-backgrounding-occluded-windows")
options.add_argument("--disable-breakpad")
options.add_argument("--disable-client-side-phishing-detection")
options.add_argument("--disable-default-apps")
options.add_argument("--disable-hang-monitor")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-prompt-on-repost")
options.add_argument("--disable-sync")
options.add_argument("--disable-translate")
options.add_argument("--metrics-recording-only")
options.add_argument("--safebrowsing-disable-auto-update")
options.add_argument("--enable-automation")
options.add_argument("--password-store=basic")
options.add_argument("--use-mock-keychain")


def open_browser() -> webdriver:
    try:
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        driver.get("https://www.barstoolsportsbook.com/sports/basketball/nba?category=live")

        login_func(driver)

        return driver

    except:
        driver.quit()
        print("Attempt to open Barstool bot failed. Trying again...")
        return open_browser()


def open_browser_after_freeze() -> webdriver:
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.get("https://www.barstoolsportsbook.com/sports/basketball/nba?category=live")

    login_func(driver)

    return driver


def try_to_place(team_to_bet, moneyline_target, driver, params) -> bool:
    # First check if we need to log back in
    try:
        check_timed_out(driver)
    except:
        pass
    click_clear_slip_button_first(driver)
    unit_size = params['STAKE']

    print(f"Barstool {team_to_bet} @{moneyline_target}, ${unit_size}")

    return get_moneyline_box(team_to_bet, moneyline_target, driver, params)


def get_moneyline_box(team, moneyline_target, driver, params) -> bool:
    if team == "Timberwolves":
        team = "T'Wolves"

    teams = driver.find_elements('xpath', '//label[contains(@aria-label, "moneyline bet type.")]')

    for team_box in teams:
        if team in team_box.get_attribute("textContent") and check_odds(moneyline_target, team_box):
            team_box.click()
            worked = make_bet(driver, params)
            return worked

    return False


def check_odds(moneyline_target, team_box) -> bool:
    site_ml = team_box.get_attribute("textContent").split("  ")[-1]

    if site_ml[0] == "+":
        site_ml = int(site_ml[1:])
    elif site_ml[0] == "-":
        site_ml = int(site_ml[1:]) * -1

    if site_ml >= moneyline_target:
        return True

    elif abs(site_ml - moneyline_target) <= 10:
        return True

    else:
        return False


def make_bet(driver, params) -> bool:
    try:
        wager_box = WebDriverWait(driver, 2).until(
            (EC.presence_of_element_located((By.XPATH, "//input[contains(@aria-label, 'Enter your wager')]"))))

        wager_box.send_keys(params["STAKE"])
    except:
        click_clear_slip_button_first(driver)
        return False

    try:
        btn = WebDriverWait(driver, 2).until(
            (EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Wager')]/ancestor::button[1]"))))
        btn.click()
        if click_done_button(driver):
            return True
        else:
            click_clear_slip_button_first(driver)
            return False
    except:
        click_clear_slip_button_first(driver)
        return False


def click_done_button(driver) -> bool:
    try:
        wait = WebDriverWait(driver, 10).until(
            (EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Done')]/ancestor::button[1]"))))
        wait.click()
        return True
    except:
        return False


def click_clear_slip_button(driver) -> bool:
    wait = driver.find_element("xpath", "//button[contains(@aria-label, 'clear all bets from betslip')]")

    wait.click()

    return True


def click_clear_slip_button_first(driver):
    try:
        clear = driver.find_element("xpath", "//button[@aria-label='clear all bets from betslip']")
        clear.click()
    except:
        pass
    try:
        yes = WebDriverWait(driver, 2).until(
                (EC.presence_of_element_located((By.XPATH,
                                                 '//span[contains(text(), "Yes")]/ancestor::button'))))
        yes.click()
    except:
        pass


def login_func(driver):
    login_button = WebDriverWait(driver, 45).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "logged-out"))
    )

    login_button.click()

    user = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="USERNAME"]')))

    user.send_keys("youngfeiler")

    pass_field = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="Password"]')))

    pass_field.send_keys("Lacrosse32$")

    login_final = driver.find_element("xpath", "//button[contains(@class, 'sign-in-btn')]")

    login_final.click()

    code = notification.wait_for_message()

    code_field = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="Authentication code"]')))

    code_field.send_keys(f'{code}')

    verify = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Verify")]')))

    verify.click()

    nba = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//div[contains(@class, "trending-icon sport_basketball white-icon")]')))

    driver.get("https://www.barstoolsportsbook.com/sports/basketball/nba?category=live")

    return


def refresh(driver):
    driver.get("https://www.barstoolsportsbook.com/sports/basketball/nba?category=live")


def check_timed_out(driver):
    try:
        button = driver.find_element("xpath",
                                     "//span[contains(@class, 'v-btn__content') and contains(text(), 'Log Back In')]/ancestor::button")
        button.click()

        user = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="USERNAME"]')))

        user.send_keys("youngfeiler")

        pass_field = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="Password"]')))

        pass_field.send_keys("Lacrosse32$")

        login_final = driver.find_element("xpath", "//button[contains(@class, 'sign-in-btn')]")

        login_final.click()

        user = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//div[contains(@class, "trending-icon sport_basketball white-icon")]')))

        user.click()

    except:
        pass


def check_reality_check(driver):
    refresh(driver)
