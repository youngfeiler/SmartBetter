import time

from selenium import webdriver
import undetected_chromedriver as uc
from selenium.common import WebDriverException, TimeoutException

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scripts import main


def open_browser() -> webdriver:
    try:
        # create a custom profile
        options = uc.ChromeOptions()

        options.add_argument('--headless')
        options.add_argument('--disable-gpu')

        driver = uc.Chrome(use_subprocess=True, options=options)
        driver.maximize_window()

        driver.get("https://www.betonline.ag/sportsbook/live-betting")

        driver.switch_to.frame("liveBettingFrame")

        return driver
    except:
        print("Attempt to open the Betonline scraper failed, trying again...")
        return open_browser()


def store_in_dict(driver, params):

    try:
        driver.set_script_timeout(20)

        # actives = WebDriverWait(driver, 40).until(
        #     EC.presence_of_element_located((By.XPATH, "//div"))
        # )

        # if len(actives) > 0:
        #     active = actives[0]
        my_dict = {}
        for team in params["NBA TEAMS"]:
            team = team.split(" ")[-1].upper()
            try:

                game = driver.find_elements(By.XPATH, f"//li[contains(@data-original-title, '{team}')]")

                game[0].click()

                teams = WebDriverWait(driver, 1).until(
                    (EC.presence_of_element_located((By.XPATH,
                                                     f"//form[@class='form-horizontal dontSplit']//span[text()='Moneyline ']/ancestor::form[@class='form-horizontal dontSplit']//div[contains(text(), '{team.upper()}')]/ancestor::li[1]")
                                                    )))

                box = driver.find_element(By.XPATH,
                                          f"//form[@class='form-horizontal dontSplit']//span[text()='Moneyline ']/ancestor::form[@class='form-horizontal dontSplit']//div[contains(text(), '{team.upper()}')]/ancestor::li[1]")

                site_ml = driver.find_element(By.XPATH,
                                              f"//form[@class='form-horizontal dontSplit']//span[text()='Moneyline ']/ancestor::form[@class='form-horizontal dontSplit']//div[contains(text(), '{team.upper()}')]/ancestor::li[1]//div[@class='odds']").text

                my_dict[team] = site_ml
                return my_dict
            except:
                pass

    except TimeoutException:
        print("Betonlineag scraper frozen... trying to reboot")
        driver.quit()
        params['SCRAPERS']['betonlineag'] = open_browser()
        print("Betonlineag scraper rebooted")

        return params


def refresh_view(driver):
    driver.switch_to.default_content()
    driver.switch_to.frame("liveBettingFrame")

    return driver
