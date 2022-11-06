from os.path import abspath, dirname, join
from datetime import datetime
from hashlib import sha1
from os import environ
import requests


OAUTH_O365_APP_URL = environ.get("OAUTH_O365_IP", "localhost")
OAUTH_GSUITE_APP_URL = environ.get("OAUTH_GOOG_IP", "localhost")


def get_logs_dir(): return join(dirname(abspath(__file__)), "logs")
def get_uuid(requester): return sha1(requester.encode()).hexdigest()
def get_timestamp(): return datetime.now().isoformat()


async def request_create_o365_token(email):
    return requests.get("http://%s/createToken?email=%s" % (OAUTH_O365_APP_URL, email))

async def request_create_gsuite_token(email):
    return requests.get("http://%s/createToken?email=%s" % (OAUTH_GSUITE_APP_URL, email))

async def request_user_o365_token(email):
    return requests.get("http://%s/users?email=%s" % (OAUTH_O365_APP_URL, email))

async def request_user_gsuite_token(email):
    return requests.get("http://%s/users?email=%s" % (OAUTH_GSUITE_APP_URL, email))

async def request_user_o365_token_refresh(email):
    return requests.get("http://%s/refreshToken?email=%s" % (OAUTH_O365_APP_URL, email))

async def request_user_gsuite_token_refresh(email):
    return requests.get("http://%s/refreshToken?email=%s" % (OAUTH_GSUITE_APP_URL, email))

async def delegate_action(func, email):
    resp = await func(email)
    return resp.json()

def sanitize(data, email):
    if not data.get("stored"):
        return {"user": email, "token_stored": False}, 400
    return {"user": email, "token_stored": True}, 201

def generic_argument_check(saas, email):
    if not saas or not email:
        return False
    return True

