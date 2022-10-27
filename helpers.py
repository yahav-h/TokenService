from os import getcwd
import urllib
from os.path import join
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from hashlib import sha1
from yaml import load, Loader


def get_local_db_path(): return join(getcwd(), 'local.db')
def getuuidx(requester): return sha1(requester.encode()).hexdigest()
def getlogfile(): return join(getcwd(), 'logs')
def gettransactionid(): return sha1(datetime.now().isoformat().encode()).hexdigest()
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
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-dev-shm-using")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36")
    chrome_options.add_argument("--headless")
    d['loggingPrefs'] = {'browser': 'ALL'}
    driver_path = ChromeDriverManager(version="latest").install()
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


def extract_params(url, logger):
    url = urllib.parse.unquote(url)
    code, state, scopes = '', '', []
    domain, *uri = url.split('?')
    for _ in url.split('&'):
        if 'code' in _:
            code = _.split('=')[-1]
        elif 'state' in _:
            state = _.split('=')[-1]
        elif 'scopes' in _:
            scopes = _.split('=')[-1].split(',').pop()
    logger.info('domain extracted : %s' % domain)
    logger.info('code extracted : %s' % code)
    logger.info('state extracted : %s' % state)
    logger.info('scopes extracted : %s' % scopes)
    return code, state, scopes


class Singleton(type):
    _instance = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance[cls]


class GapiBase(object, metaclass=Singleton):
    base = None
    saas_object = None
    credential_object = None

    def __init__(self, lib, SAAS_OBJECT, CREDENTIAL_OBJECT):
        super(GapiBase, self).__init__()
        self.saas_object = SAAS_OBJECT
        self.credential_object = CREDENTIAL_OBJECT
        self.base = lib

    def from_client_config(self):
        self.base.flow.Flow.from_client_config(
            self.saas_object['web'],
            scopes=self.saas_object['app_scopes']
        )
        self.base.redirect_uri = self.saas_object['redirect_uri']
        sign_in_url, state = self.base.authorization_url(self.saas_object['web']["authorize_url"], prompt='login')
        return sign_in_url, state

    def fetch_token(self, code):
        token = self.lib.fetch_token(code=code)
        return token
