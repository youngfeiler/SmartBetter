import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scripts import main

import undetected_chromedriver as uc
# create a custom profile
options = uc.ChromeOptions()

options.add_argument('--headless')
options.add_argument('--disable-gpu')


def open_browser():
    driver = uc.Chrome(options=options, use_subprocess=True)

    # driver = uc.Chrome(options=options)
    driver.maximize_window()
    driver.get("https://sports.co.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004")

    return driver



def find_game_divs(driver):
    divs = driver.find_elements("xpath", "//div[contains(@class, 'grid-event-wrapper')]")

    print(len(divs))




