import time

from selenium import webdriver
import undetected_chromedriver as uc
from selenium.common import WebDriverException, TimeoutException

from scripts import main

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def open_browser() -> webdriver:
    try:
        # create a custom profile
        options = uc.ChromeOptions()

        options.add_argument('--headless')
        options.add_argument('--disable-gpu')

        driver = uc.Chrome(options=options, use_subprocess=True)

        driver.maximize_window()

        driver.get("https://www.barstoolsportsbook.com/sports/basketball/nba?category=live")

        teams = WebDriverWait(driver, 10).until(
            (EC.presence_of_element_located((By.XPATH, '//label[contains(@aria-label, "moneyline bet type.")]'))))

        return driver
    except:
        driver.quit()
        print("Attempt to open the Barstool scraper failed, trying again...")
        return open_browser()


def store_in_dict(driver, params):

    try:
        driver.set_script_timeout(10)
        my_dict = {}

        for team in params['NBA TEAMS']:
            team = team.split(" ")[-1]


            if team == "Timberwolves":
                team = "T'Wolves"
            try:
                team_box = driver.find_element('xpath',  f'//label[contains(@aria-label, "moneyline bet type.") and contains(@aria-label, "{team}")]')

                ml = team_box.get_attribute("textContent").split("  ")[-1]

                if team == "T'Wolves":
                    team = "Timberwolves"

                my_dict[team] = ml
            except:
                pass

        return my_dict

    except TimeoutException:
        print("Barstool scraper frozen... trying to reboot")
        driver.quit()
        params['SCRAPERS']['barstool'] = open_browser()
        print("Barstool rebooted")
        return params


