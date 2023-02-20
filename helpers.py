from os.path import abspath, dirname, join
from datetime import datetime
from hashlib import sha1
from os import environ
import requests
from logging.handlers import RotatingFileHandler
import logging


def get_logs_dir(): return join(dirname(abspath(__file__)), "logs")
def get_uuid(requester): return sha1(requester.encode()).hexdigest()
def get_timestamp(): return datetime.now().isoformat()


logging.Formatter(logging.BASIC_FORMAT)
logger = logging.getLogger('ServiceLogger')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    filename='%s/runtime.log' % get_logs_dir(),
    maxBytes=8182,
    backupCount=5
)
logger.addHandler(handler)


OAUTH_O365_APP_URL = environ.get("OAUTH_O365_IP", "oauth-o365.avanan-dev.net")
OAUTH_GSUITE_APP_URL = environ.get("OAUTH_GOOG_IP", "oauth-gsuite.avanan-dev.net")


async def request_create_o365_token(email, client_ip):
    logger.info(
        "%s | %s | request_create_o365_token | params(%s, %s)" % (client_ip, datetime.now().isoformat(), OAUTH_O365_APP_URL, email)
    )
    resp = requests.get("http://%s/createToken?email=%s" % (OAUTH_O365_APP_URL, email))
    logger.info(
        "%s | %s | request_create_o365_token | returns(%s)" % (client_ip, datetime.now().isoformat(), resp.content)
    )
    return resp

async def request_create_gsuite_token(email, client_ip):
    logger.info(
        "%s | %s | request_create_gsuite_token | params(%s, %s)" % (client_ip, datetime.now().isoformat(), OAUTH_GSUITE_APP_URL, email)
    )
    resp = requests.get("http://%s/createToken?email=%s" % (OAUTH_GSUITE_APP_URL, email))
    logger.info(
        "%s | %s | request_create_gsuite_token | returns(%s)" % (client_ip, datetime.now().isoformat(), resp.content)
    )
    return resp

async def request_user_o365_token(email, client_ip):
    logger.info(
        "%s | %s | request_user_o365_token | params(%s, %s)" % (client_ip, datetime.now().isoformat(), OAUTH_O365_APP_URL, email)
    )
    resp = requests.get("http://%s/users?email=%s" % (OAUTH_O365_APP_URL, email))
    logger.info(
        "%s | %s | request_user_o365_token | returns(%s)" % (client_ip, datetime.now().isoformat(), resp.content)
    )
    return resp

async def request_user_gsuite_token(email, client_ip):
    logger.info(
        "%s | %s | request_user_gsuite_token | params(%s, %s)" % (client_ip, datetime.now().isoformat(), OAUTH_GSUITE_APP_URL, email)
    )
    resp = requests.get("http://%s/users?email=%s" % (OAUTH_GSUITE_APP_URL, email))
    logger.info(
        "%s | %s | request_user_gsuite_token | returns(%s)" % (client_ip, datetime.now().isoformat(), resp.content)
    )
    return resp

async def request_user_o365_token_refresh(email, client_ip):
    logger.info(
        "%s | %s | request_user_o365_token_refresh | params(%s, %s)" % (client_ip, datetime.now().isoformat(), OAUTH_O365_APP_URL, email)
    )
    resp = requests.get("http://%s/refreshToken?email=%s" % (OAUTH_O365_APP_URL, email))
    logger.info(
        "%s | %s | request_user_o365_token_refresh | returns(%s)" % (client_ip, datetime.now().isoformat(), resp.content)
    )
    return resp

async def request_user_gsuite_token_refresh(email, client_ip):
    logger.info(
        "%s | %s | request_user_gsuite_token_refresh (params: %s, %s)" % (client_ip, datetime.now().isoformat(), OAUTH_GSUITE_APP_URL, email)
    )
    resp = requests.get("http://%s/refreshToken?email=%s" % (OAUTH_GSUITE_APP_URL, email))
    logger.info(
        "%s | %s | request_user_gsuite_token_refresh | returns(%s)" % (client_ip, datetime.now().isoformat(), resp.content)
    )
    return resp

async def delegate_action(func, email, client_ip):
    logger.info("%s | %s | delegate_action | params(%s, %s)" % (client_ip, datetime.now().isoformat(), func, email))
    resp = await func(email)
    logger.info("%s | %s | delegate_action | returns(%s, %s)" % (client_ip, datetime.now().isoformat(), func, resp.content))
    return resp.json()

def sanitize(data, email, client_ip):
    logger.info("%s | %s | sanitize | params(%s, %s)" % (client_ip, datetime.now().isoformat(), data, email))
    if not data.get("stored"):
        resp = {"user": email, "token_changed": False}, 400
        logger.info("%s | %s | sanitize | returns(%s)" % (client_ip, datetime.now().isoformat(), resp))
        return resp
    resp = {"user": email, "token_changed": True}, 201
    logger.info("%s | %s | sanitize | returns(%s)" % (client_ip, datetime.now().isoformat(), resp))
    return resp

def generic_argument_check(saas, email, client_ip):
    logger.info("%s | %s | generic_argument_check | params(%s, %s)" % (client_ip, datetime.now().isoformat(), saas, email))
    if not saas or not email:
        logger.info("%s | %s | generic_argument_check | returns(False)" % (client_ip, datetime.now().isoformat()))
        return False
    logger.info("%s | %s | generic_argument_check | returns(True)" % (client_ip, datetime.now().isoformat()))
    return True

