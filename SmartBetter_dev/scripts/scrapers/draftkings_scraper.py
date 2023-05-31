import time

from selenium.common import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


def open_browser():
    try:
        # create a custom profile
        options = uc.ChromeOptions()

        options.add_argument('--headless')
        options.add_argument('--disable-gpu')

        driver = uc.Chrome(options=options, use_subprocess=True)

        driver.maximize_window()

        driver.get("https://sportsbook.draftkings.com/leagues/basketball/nba")

        return driver
    except:
        print("Attempt to open the DraftKings scraper failed, trying again...")
        return open_browser()



def store_in_dict(driver, params):

    try:
        driver.set_script_timeout(10)

        actives = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, f'//div[@class="event-cell__name-text"]'))
        )

        my_dict = {}

        for team in params['NBA TEAMS']:
            team = team.split(" ")[-1]
            try:
                ml = driver.find_elements('xpath',
                                         f'//div[@class="event-cell__name-text"][contains(text(), "{team}")]/ancestor::tr//td[3]')[0].get_attribute("textContent")
                my_dict[team] = ml
            except:
                pass

        return my_dict

    except TimeoutException:

        print("Draftkings scraper frozen... trying to reboot")
        driver.quit()
        params['SCRAPERS']['draftkings'] = open_browser()
        print("Draftkings rebooted")

        return params

