#python -m PyInstaller --onefile --hidden-import webdriver_manger ppl_data_pull.py

import time
import os
import pytz
from datetime import datetime, date, timedelta

import toml
from signal import signal, SIGINT
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
#from selenium.webdriver.firefox.options import Options as FirefoxOptions
#from selenium.webdriver.firefox.service import Service as FirefoxService
#from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from time import perf_counter

import re
import csv
import pandas as pd

import logging
import sys
from logging.handlers import RotatingFileHandler

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

CONFIG_FILE_NAME = ".\\settings\\config_pge.toml"

RUNNING = True

def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected.')
    print('Cleaning up...')
    global RUNNING
    RUNNING = False



def is_unity_login(browser, url, usernameId, username, passwordId, password, submit_buttonId):

    browser.get(url)

    error = None
    try:

        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.NAME, usernameId))).send_keys(username)
        #browser.execute_script("arguments[0].sendKeys({});".format(username), el_user)
        browser.find_element(By.NAME, passwordId).send_keys(password)
        browser.find_element(By.ID, submit_buttonId).click()


        try:
            error = browser.find_element(By.ID, "loginError")
        except NoSuchElementException:
            pass
        if error:
            logging.info(f"Error: {error.text}")
            return False
    except NoSuchElementException:
        print('no such element')
        return False
    return True





def main(app_config):
    global RUNNING

    throttle = app_config.get('THROTTLE')
    headless = app_config.get("HEADLESS")
    username = app_config.get("USERNAME")
    password = app_config.get("PASSWORD")
    output_loc = app_config.get('OUTPUT_LOC')





    chromeOptions = Options()
    chromeOptions.headless = headless
    '''
    chromeOptions.add_argument('window-size=1920,1080')
    chromeOptions.add_argument("--start-maximized")
    chromeOptions.add_argument('--ignore-certificate-errors')
    chromeOptions.add_argument("--no-sandbox")
    chromeOptions.add_argument("--disable-gpu")
    chromeOptions.add_argument('--lang=en')
    chromeOptions.add_argument('disable-blink-features=AutomationControlled')
    user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.2'
    chromeOptions.add_argument(f'user-agent={user_agent}')
    '''


    print("Opening browser...")
    #browser = webdriver.Chrome(executable_path="./drivers/chromedriver", options=chromeOptions)
    s=Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=s, options=chromeOptions)
    #s=service=FirefoxService(GeckoDriverManager().install())
    #browser = webdriver.Firefox(service=s, options=fireFoxOptions)
    browser.maximize_window()


    print("Running in background, first page may take longer to load than subsequent pages")
    print("Press CTRL-C to exit")

    #initialize blank data frame:
    yesterday_ts = datetime.today() - timedelta(days=2)
    yesterday_ts=yesterday_ts.strftime('%m/%d/%Y')
    today_ts = datetime.today() - timedelta(days=1)
    today_ts = datetime.today().strftime('%m/%d/%Y')


    try:
        print('logging in')
        url='https://portlandgeneral.com/auth/sign-in'
        logged_in = is_unity_login(browser, url, "email", username,
                                       "password", password,
                                       "sign-in-submit-btn")

        if logged_in:
            print("Successfully logged in")
            #myElem = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.ID, "main")))


    except Exception as e:
        print("An exception happened")
        print(e)
    if RUNNING:
        print(f"Sleeping for {throttle} seconds...")
        time.sleep(throttle)


    #target account dropdown
    is_loading =True

    while is_loading:

        browser.get("https://portlandgeneral.com/secure/account/summary#energyUse")
        action=ActionChains(browser)
        wait=WebDriverWait(browser,20)

        #switch to iframe "energy_cost_trends"
        iframe1 = wait.until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@id='energy_cost_trends']")))
        iframe2 = wait.until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@id='energy_cost_trends-frame']")))
        print("Frame successfully opened")

        WebDriverWait(browser, 150).until(
            EC.invisibility_of_element_located((By.ID, "loading")))

        a = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//span[contains(.,'Over Time')]")))

        #print(a)
        #action.move_to_element(a)




        eng=wait.until(EC.presence_of_element_located((By.ID, "cost_over_time_usage_1_energy_types_1")))
        browser.execute_script("arguments[0].click();", eng)

        elec=wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(.,'Electricity Usage')]")))
        browser.execute_script("arguments[0].click();", elec)

        WebDriverWait(browser, 150).until(
            EC.invisibility_of_element_located((By.ID, "loading")))

        #time.sleep(60)

        # open download window
        a=wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "track-button-export-green-button-csv-download")))
        browser.execute_script("arguments[0].click();", a)



        WebDriverWait(browser, 150).until(
            EC.invisibility_of_element_located((By.ID, "loading")))
        #input dates
        input = wait.until(
            EC.element_to_be_clickable((By.NAME, "green_button_form[start_green_button_date_range]")))
        input.clear()
        input.send_keys(yesterday_ts)
        output = wait.until(
            EC.element_to_be_clickable((By.NAME, "green_button_form[end_green_button_date_range]")))
        output.clear()
        output.send_keys(today_ts)


        wait.until(EC.presence_of_element_located((By.XPATH, "//button[@class='btn btn-primary green-button-download']"))).click()
        time.sleep(10)


        browser.quit()
        is_loading=False



if __name__ == "__main__":

    signal(SIGINT, handler)
    app_config = toml.load(CONFIG_FILE_NAME)
    # SET LOGGER
    mydir = app_config.get("LOG_LOC")
    rfh = RotatingFileHandler(
        filename=mydir + '\\pge.log',
        mode='a',
        maxBytes=5 * 1024 * 1024,
        backupCount=1,
        encoding=None,
        delay=0
    )
    rfh.namer = lambda name: name.replace(".log", "") + ".log"
    logging.basicConfig(encoding='utf-8', level=logging.INFO, handlers=[rfh])

    logging.info('Configuration file successfully loaded.')
    logging.info('Current datetime: {}'.format(datetime.now()))


    #################
    # log uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        print("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


    sys.excepthook = handle_exception

    main(app_config)
    logging.info("Program finished successfully!")

