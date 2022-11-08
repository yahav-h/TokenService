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


async def request_create_o365_token(email):
    logger.info("request_create_o365_token (params: %s, %s)" % (OAUTH_O365_APP_URL, email))
    return requests.get("http://%s/createToken?email=%s" % (OAUTH_O365_APP_URL, email))

async def request_create_gsuite_token(email):
    logger.info("request_create_gsuite_token (params: %s, %s)" % (OAUTH_GSUITE_APP_URL, email))
    return requests.get("http://%s/createToken?email=%s" % (OAUTH_GSUITE_APP_URL, email))

async def request_user_o365_token(email):
    logger.info("request_user_o365_token (params: %s, %s)" % (OAUTH_O365_APP_URL, email))
    return requests.get("http://%s/users?email=%s" % (OAUTH_O365_APP_URL, email))

async def request_user_gsuite_token(email):
    logger.info("request_user_gsuite_token (params: %s, %s)" % (OAUTH_GSUITE_APP_URL, email))
    return requests.get("http://%s/users?email=%s" % (OAUTH_GSUITE_APP_URL, email))

async def request_user_o365_token_refresh(email):
    logger.info("request_user_o365_token_refresh (params: %s, %s)" % (OAUTH_O365_APP_URL, email))
    return requests.get("http://%s/refreshToken?email=%s" % (OAUTH_O365_APP_URL, email))

async def request_user_gsuite_token_refresh(email):
    logger.info("request_user_gsuite_token_refresh (params: %s, %s)" % (OAUTH_GSUITE_APP_URL, email))
    return requests.get("http://%s/refreshToken?email=%s" % (OAUTH_GSUITE_APP_URL, email))

async def delegate_action(func, email):
    logger.info("delegate_action (params: %s, %s)" % (func, email))
    resp = await func(email)
    logger.info("%s (return: %s)" % (func, resp.content))
    return resp.json()

def sanitize(data, email):
    if not data.get("stored"):
        return {"user": email, "token_stored": False}, 400
    return {"user": email, "token_stored": True}, 201

def generic_argument_check(saas, email):
    if not saas or not email:
        return False
    return True

