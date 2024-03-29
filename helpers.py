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
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, field, asdict
import logging

logging.Formatter(logging.BASIC_FORMAT)
logger = logging.getLogger('ServiceLogger')
logger.setLevel(logging.DEBUG)


@dataclass
class SaasProperties(object):
    provider: str = field(init=True)
    app_id: str = field(init=False)
    app_sec: str = field(init=False)
    auth_url: str = field(init=False)
    token_url: str = field(init=False)
    redirect_url: str = field(init=False)
    app_scopes: str = field(init=False)
    def __repr__(self): return "<Properties %r>" % asdict(self)

    def __init__(self, provider, **kw):
        self.provider = provider
        if "microsoft" == self.provider:
            props = getoauth2properties("office365", kw['request'])
            self.redirect_url = props['redirect_uri']
            self.app_id = props['app_id']
            self.app_sec = props['app_sec']
            self.token_url = props['token_url']
            self.auth_url = props['authorize_url']
            self.app_scopes = props['app_scopes']
        elif "google" == self.provider:
            props = getoauth2properties("gsuite", kw['request'])
            self.redirect_url = props['web']['redirect_uris'][0]
            self.app_id = props['web']['client_id']
            self.app_sec = props['web']['client_secret']
            self.token_url = props['web']['token_uri']
            self.auth_url = props['web']['auth_uri']
            self.app_scopes = '+'.join(props['app_scopes'])

def get_requester_ip(request): return request.client.host
def get_logs_dir(): return join(getcwd(), "logs")
def get_local_db_path(): return join(getcwd(), 'local.db')
def getuuidx(requester): return sha1(requester.encode()).hexdigest()
def gettransactionid(): return sha1(datetime.now().isoformat().encode()).hexdigest()
def gettimestamp(): return datetime.now().isoformat()


handler = RotatingFileHandler(
    filename='%s/runtime.log' % get_logs_dir(),
    maxBytes=818200,
    backupCount=5
)
logger.addHandler(handler)


def get_props_params_by_email_provider(this_email, request):
    if "onmicrosoft.com" in this_email or "outlook.com" in this_email:
        return SaasProperties("microsoft", request=request)
    if "avanan.net" in this_email or "gmail.com" in this_email:
        return SaasProperties("google", request=request)


def getdatatbaseinfo():
    with open(join(getcwd(), 'resources', 'properties.yml'), 'r') as out_stream:
        data = load(out_stream, Loader)
        return data['database']


def getoauth2properties(saas, request):
    logger.info(
        f"host={get_requester_ip(request)},  timestamp={gettimestamp()}, func=getoauth2properties, " +
        f"params=({saas})"
    )
    with open(join(getcwd(), 'resources', 'properties.yml'), 'r') as out_stream:
        data = load(out_stream, Loader)
        logger.info(
            f"host={get_requester_ip(request)}, timestamp={gettimestamp()}, func=getoauth2properties, " +
            f"returns=({data['oauth2'][saas]})"
        )
        return data['oauth2'][saas]


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
    logger.info(
        f"timestamp={gettimestamp()}, func=getwebdriver, driverconfig=({str(chrome_options)}), returns={driver}"
    )
    return driver


def getemailaddressandpassword(alias, tenant, saas):
    with open(join(getcwd(), 'resources', 'properties.yml'), 'r') as out_stream:
        data = load(out_stream, Loader)
        pwd = data["security"][saas]
        email = "%s@%s.%s" % (alias, tenant, data["domains"][saas])
        match = (email, pwd)
    return match


def extract_params(url, request):
    logger.info(
        f"host={get_requester_ip(request)}, timestamp={gettimestamp()}, func=extract_params, " +
        f"params=({url})"
    )
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
    logger.info(
        f"host={get_requester_ip(request)}, timestamp={gettimestamp()}, func=extract_params, " +
        f"returns=({code}, {state}, {scopes})"
    )
    print('Extract Params : %r' % [domain, code, state, scopes])
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
