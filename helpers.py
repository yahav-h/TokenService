from os import getcwd
from os.path import join
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from datetime import datetime
from hashlib import md5
from yaml import load, Loader

def gettransactionid(): return md5(datetime.now().isoformat().encode()).hexdigest()
def gettimestamp(): return datetime.now().isoformat()

def getdatatbaseinfo():
    with open(join(getcwd(), 'resources', 'properties.yml'), 'r') as out_stream:
        data = load(out_stream, Loader)
        return data['database']

def getoauth2properties():
    with open(join(getcwd(), 'resources', 'properties.yml'), 'r') as out_stream:
        data = load(out_stream, Loader)
        return data['oauth2']

def getwebdriver():
    driver_path = join(getcwd(), 'resources', 'chromedriver')
    chrome_options = Options()
    d = DesiredCapabilities.CHROME
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    d['loggingPrefs'] = {'browser': 'ALL'}
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36")
    driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options, desired_capabilities=d)
    driver.delete_all_cookies()
    return driver

def getemailaddressandpassword(alias, tenant, saas):
    with open(join(getcwd(), 'resources', 'properties.yml'), 'r') as out_stream:
        data = load(out_stream, Loader)
        pwd = data["security"][saas]
        email = "%s@%s.%s" % (alias, tenant, data["domains"][saas])
        match = (email, pwd)
    return match
