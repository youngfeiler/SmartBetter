import time

from selenium.common import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# create a custom profile
from scripts import draftkings



from selenium import webdriver


# configure the profile to store cookies and cache
# options.add_experimental_option("detach", True)
# options.add_argument("--use-fake-ui-for-media-stream")
# options.add_argument("--use-fake-device-for-media-stream")
# options.add_argument("--disable-extensions")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-popup-blocking")
# options.add_argument("start-maximized")
# options.add_argument("disable-infobars")
# options.add_argument("--disable-web-security")
# options.add_argument("--disable-notifications")
# options.add_argument("--enable-automation")
# options.add_argument("--disable-background-timer-throttling")
# options.add_argument("--disable-backgrounding-occluded-windows")
# options.add_argument("--disable-breakpad")
# options.add_argument("--disable-client-side-phishing-detection")
# options.add_argument("--disable-default-apps")
# options.add_argument("--disable-hang-monitor")
# options.add_argument("--disable-popup-blocking")
# options.add_argument("--disable-prompt-on-repost")
# options.add_argument("--disable-sync")
# options.add_argument("--disable-translate")
# options.add_argument("--metrics-recording-only")
# options.add_argument("--safebrowsing-disable-auto-update")
# options.add_argument("--enable-automation")
# options.add_argument("--password-store=basic")
# options.add_argument("--use-mock-keychain")

def open_browser():
    try:
        options = uc.ChromeOptions()
        #
        # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')

        driver = uc.Chrome(options=options, use_subprocess=True)

        # driver = uc.Chrome(options=options)
        driver.maximize_window()
        driver.get("https://sportsbook.draftkings.com/leagues/basketball/nba")

        login_func(driver)

        return driver
    except:
        driver.quit()
        return open_browser()

def reboot():
    try:
        options = uc.ChromeOptions()
        #
        # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')

        driver = uc.Chrome(options=options, use_subprocess=True)

        # driver = uc.Chrome(options=options)
        driver.maximize_window()
        driver.get("https://sportsbook.draftkings.com/leagues/basketball/nba")

        login_func(driver)

        time.sleep(2)

        return driver
    except:
        print("Attempt to open DraftKings bot failed. Trying again...")
        return reboot()



def try_to_place(team_to_bet, moneyline_target, driver, params):

    unit_size = params['STAKE']

    print(f"DraftKings {team_to_bet} @{moneyline_target}, ${unit_size}")

    return get_moneyline_box(team_to_bet, moneyline_target, driver, params)


def get_moneyline_box(team_to_bet, moneyline_target, driver, params):


    teams = driver.find_elements('xpath',
                                 f'//div[@class="event-cell__name-text"][contains(text(), "{team_to_bet}")]/ancestor::tr//td[3]')

    if check_odds(moneyline_target, teams[0]):
        teams[0].click()

        worked = make_bet(driver, params)

        return worked


def check_odds(moneyline_target, team_box):
    site_ml = team_box.get_attribute("textContent")

    if site_ml[0] == "+":
        site_ml = int(site_ml[1:])
    elif site_ml[0] == "−":
        site_ml = int(site_ml[1:]) * -1

    if site_ml >= moneyline_target:
        return True

    elif abs(site_ml - moneyline_target) <= 10:
        return True

    else:
        return False


def make_bet(driver, params):


    try:
        driver.set_script_timeout(30)

        test = WebDriverWait(driver, 20).until(
            (EC.element_to_be_clickable((By.XPATH, "//div"))))

        try:
            wager_box = WebDriverWait(driver, 20).until(
                (EC.element_to_be_clickable((By.XPATH, "//input[@id='betslip-wager-box__input-0']"))))
            wager_box.send_keys(params["STAKE"])
            try:
                submit = WebDriverWait(driver, 10).until(
                    (EC.element_to_be_clickable((By.XPATH, "//div[@class='dk-place-bet-button__wrapper']"))))
                submit.click()
                if click_done_button(driver):
                    return True
                else:
                    click_clear_slip_button(driver)
                    return False
            except:
                click_clear_slip_button(driver)
                return False

        except:
            click_clear_slip_button(driver)
            return False
    except TimeoutException:

        print("Draftkings bot frozen... trying to reboot")
        driver.quit()
        params["DRIVERS"]['draftkings'] = reboot()
        print("Draftkings bot rebooted")
        return params


def click_done_button(driver):
    try:
        done = WebDriverWait(driver, 10).until(
            (EC.element_to_be_clickable((By.XPATH, "//div[@class='dk-betslip-receipt__header-close-icon']"))))
        done.click()
        return True
    except:
        return False

def click_clear_slip_button(driver):
    wait = WebDriverWait(driver, 3).until(
        (EC.element_to_be_clickable((By.XPATH, "//div[@class='dk-betslip-header__clear-all']"))))
    wait.click()
    time.sleep(1)
    yes = WebDriverWait(driver, 5).until(
        (EC.element_to_be_clickable((By.XPATH,
                                     '//div[@class="dk-betslip-confirm-clear-all__confirm-button"]'))))
    yes.click()

    return True


def login_func(driver):
    login_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[text()='Log In']"))
    )

    login_button.click()

    user = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@id="login-username-input"]')))

    user.send_keys("stefantfeiler@gmail.com")

    pass_field = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@id="login-password-input"]')))

    pass_field.send_keys("Lacrosse32$")

    login_final = driver.find_element("xpath", "//button[@id='login-submit']")

    login_final.click()

    return


def check_timed_out(driver):
    try:
        btn = driver.find_elements('xpath', f'//button[contains(text(), "Log Back In")]')
        btn.click()

        user = WebDriverWait(driver, 2).until(
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

        return

    except:
        pass


def refresh(driver):
    driver.get("https://sportsbook.draftkings.com/leagues/basketball/nba")
