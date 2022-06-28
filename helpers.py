from os import getcwd
from os.path import join
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
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
    chrome_options = Options()
    d = DesiredCapabilities.CHROME
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless")
    d['loggingPrefs'] = {'browser': 'ALL'}
    driver_path = ChromeDriverManager().install()
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
