from datetime import datetime
from hashlib import sha1
import requests

def get_uuid(requester): return sha1(requester.encode()).hexdigest()
def get_timestamp(): return datetime.now().isoformat()


async def request_create_o365_token(email):
    url = "http://localhost/createToken?email=%s" % email
    return requests.get(url)

async def request_create_gsuite_token(email):
    url = "http://localhost/createToken?email=%s" % email
    return requests.get(url)

async def request_user_o365_token(email):
    url = "http://localhost/users?email=%s" % email
    return requests.get(url)

async def request_user_gsuite_token(email):
    url = "http://localhost/users?email=%s" % email
    return requests.get(url)

async def request_user_o365_token_refresh(email):
    url = "http://localhost/refreshToken?email=%s" % email
    return requests.get(url)

async def request_user_gsuite_token_refresh(email):
    url = "http://localhost/refreshToken?email=%s" % email
    return requests.get(url)

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

