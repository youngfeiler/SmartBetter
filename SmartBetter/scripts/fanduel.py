import datetime
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common import actions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


# create a custom profile
options = webdriver.ChromeOptions()
# configure the profile to store cookies and cache
options.add_experimental_option("detach", True)
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
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36")



def open_browser():
    driver = webdriver.Chrome(options=options)
    #driver = webdriver.Chrome("/Users/stefanfeiler/PycharmProjects/autobet_placer_1/23/SmartBetter_PROD/drivers/fanduel", chrome_options=chrome_options)

    driver.get("https://sportsbook.fanduel.com/navigation/nba")

    login_input = input("Are you logged in to Fanduel?")

    if login_input.upper() == "YES":

        return driver


def try_to_place(team, driver, params):

    team_to_bet = team['team']
    moneyline_target = team['moneyline']
    unit_size = params['STAKE']
    is_live = team['live']

    print(f"{team['bookie']}: {team_to_bet} {moneyline_target}, {unit_size}, {is_live}")

    #check_url(is_live, driver)

    return get_moneyline_box(team_to_bet, moneyline_target, driver, params)




def check_url(bool, driver):

    if bool == False:
        if driver.current_url != "https://sportsbook.fanduel.com/navigation/nba":
            live_tab_links = driver.find_elements('xpath', '//div[@class="v-tab"]')
            live_tab_links[0].click()

    if bool == True:
        if driver.current_url != "https://sportsbook.fanduel.com/navigation/nba":
            live_tab_links = driver.find_elements('xpath', '//div[@class="v-tab"]')
            live_tab_links[0].click()

def get_moneyline_box(team_to_bet, moneyline_target, driver, params):

    team = team_to_bet.split(' ')[-1]

    team_ml = driver.find_element('xpath', f'//label[contains(@aria-label, "Moneyline,") and contains(@aria-label, "{team}")]').get_attribute("textContent")

    for team_box in teams:
        if team in team_box.get_attribute("textContent") and check_odds(driver, moneyline_target, team_box, params):
            team_box.click()
            worked = make_bet(driver, params)
            return worked



def check_odds(driver, moneyline_target, team_box, params):

    site_ml = team_box.get_attribute("textContent").split("  ")[1]

    if site_ml[0] =="+":
        site_ml = int(site_ml[1:])
    elif site_ml[0] =="-":
        site_ml = int(site_ml[1:]) * -1

    if site_ml >= moneyline_target:
        return True

    elif abs(site_ml - moneyline_target) <= 10:
        return True

    else:
        return False


def make_bet(driver, params):
    wager_span = WebDriverWait(driver, 2).until(
        (EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'WAGER'))]"))))
    parent_div = wager_span.find_element_by_xpath("..")
    wager_box = parent_div.find_element_by_xpath("./div/input")

    wager_box.send_keys(params["STAKE"])

    clicked = False

    try:
        button = WebDriverWait(driver, 3).until((EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Place 1 bet for')]"))))
        button.click()
        clicked = True
        done = WebDriverWait(driver, 8).until((EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Done')]"))))
        done.click()
        return True
    except:
        clear_betslip(driver)
        return False




def clear_betslip(driver):
    clear = driver.find_elements('xpath', "//span[contains(text(),'Done')]")
    clear.click()






