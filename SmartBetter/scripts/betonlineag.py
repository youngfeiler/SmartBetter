import time

import undetected_chromedriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver import Keys
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


# # configure the profile to store cookies and cache
# options.add_argument("--use-fake-ui-for-media-stream")
# options.add_argument("--use-fake-device-for-media-stream")
# options.add_argument("--disable-extensions")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-popup-blocking")
# options.add_argument("--disable-web-security")
# options.add_argument("--disable-notifications")
# options.add_argument("--password-store=basic")
# options.add_argument("--use-mock-keychain")


def open_browser() -> undetected_chromedriver:
    try:
        options = uc.ChromeOptions()

        driver = uc.Chrome(use_subprocess=True, options=options)
        driver.maximize_window()
        driver.get("https://betonline.ag/sportsbook/live-betting")

        login_func(driver)

        return driver

    except:
        driver.quit()
        print("Attempt to open BetOnline bot failed. Trying again...")
        return open_browser()

def reboot() -> undetected_chromedriver:
    try:
        options = uc.ChromeOptions()

        options.add_argument('--headless')
        options.add_argument('--disable-gpu')

        driver = uc.Chrome(executable_path="//drivers/fanduel",
                           use_subprocess=True, options=options)
        driver.maximize_window()
        driver.get("https://betonline.ag/sportsbook/live-betting")

        login_func(driver)

        time.sleep(2)

        return driver
    except:
        print("Attempt failed, trying again")
        return reboot()


def try_to_place(team, driver, params):
    
    if not team['is_live']:
        return False
    
    team_to_bet = team['team']
    
    moneyline_target = team['moneyline']
    
    unit_size = params['STAKE'] * 10

    is_live = team['is_live']

    print(f"BetOnline {team_to_bet} @{moneyline_target}, ${unit_size} {is_live}")

    return get_moneyline_box(team_to_bet, moneyline_target, driver, params)


def get_moneyline_box(team_to_bet, moneyline_target, driver, params):
    try:
        driver.set_script_timeout(30)

        # test = WebDriverWait(driver, 40).until(
        #     (EC.element_to_be_clickable((By.XPATH, "//div"))))

        team = team_to_bet.upper()

        driver = refresh_view(driver)

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
        if check_odds(moneyline_target, site_ml):
            box.click()
            wait = WebDriverWait(driver, 20).until(
                (EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Close')]"))))

            try:
                success = driver.find_element(By.XPATH, "//h3[contains(text(), 'Bet Posted!')]")
                wait.click()
                driver.switch_to.default_content()
                return True
            except NoSuchElementException:
                try:
                    acc = WebDriverWait(driver, 2).until(
                        (EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Accept')]"))))
                    acc.click()
                except:
                    print("")
                wait.click()
                try:
                    bets_in_slip = driver.find_elements(By.XPATH, "//div[@class='closeWinButton']")
                    for bet in bets_in_slip:
                        bet.click()
                except:
                    print("")
                driver.switch_to.default_content()
                return False
        else:
            driver.switch_to.default_content()
            return False
    except TimeoutException:

        print("Betonline bot frozen... trying to reboot")
        driver.quit()
        params["DRIVERS"]['betonlineag'] = reboot()
        print("Betonline bot rebooted")

        return params


def check_odds(moneyline_target, site_ml):
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


def login_func(driver):
    login_button = WebDriverWait(driver, 45).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@id='btnOpenLogin']"))
    )

    login_button.click()

    email_field = WebDriverWait(driver, 45).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@id='username']"))
    )

    email_field.send_keys("stefantfeiler@gmail.com")

    pass_field = WebDriverWait(driver, 45).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@id='password']"))
    )

    pass_field.send_keys("Lacrosse32$")

    box = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@id='rememberMe']"))
    )

    box.click()

    login_final = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "kc-login"))
    )

    login_final.click()

    time.sleep(8)

    driver = refresh_view(driver)

    money = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='inputAmount']"))
    )

    money.clear()

    money.send_keys(10)

    box = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@name='switchQuickBet']"))
    )

    box.click()

    time.sleep(1)

    driver = refresh_view(driver)

    accept = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Accept')]"))
    )

    accept.click()

    return


def get_site(driver):
    driver.get("https://betonline.ag/sportsbook/live-betting")


def refresh_view(driver):
    driver.switch_to.default_content()
    driver.switch_to.frame("liveBettingFrame")

    return driver
