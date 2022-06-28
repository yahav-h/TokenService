from fastapi import FastAPI
from fastapi.background import BackgroundTasks
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette_context import context, plugins
from starlette_context.middleware import ContextMiddleware
from requests_oauthlib import OAuth2Session
from mso_login_page import MSOLoginPage
from helpers import getoauth2properties, getwebdriver, getemailaddressandpassword, gettransactionid, gettimestamp
from datatypes import TokenUserRecords
from database import db_session
from uvicorn import run
import pickle
import os


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'

global callback_value
global transactions
callback_value = None
transactions = {
    "pending": {},
    "done": {}
}

middleware = [
    Middleware(
        ContextMiddleware,
        plugins=(
            plugins.RequestIdPlugin(),
            plugins.CorrelationIdPlugin()
        )
    )
]

app = FastAPI(middleware=middleware)

def update_user_token_routine(email):
    global callback_value
    global transactions
    try:
        optional: TokenUserRecords = TokenUserRecords.query.filter_by(user=email).first()
        if not optional:
            record = TokenUserRecords(user=email, token=callback_value)
        else:
            record = optional
            record.token = pickle.dumps(callback_value)
        db_session.add(record)
        db_session.commit()
        transactions["done"][email] = transactions["pending"].pop(email)
        callback_value = None
        return True
    except:
        return False

def renew_task(email, password):
    props = getoauth2properties()
    aad_auth = OAuth2Session(props["app_id"], scope=props["app_scopes"], redirect_uri=props["redirect_uri"])
    sign_in_url, state = aad_auth.authorization_url(props["authorize_url"], prompt='login')
    webdriver = getwebdriver()
    page = MSOLoginPage(webdriver)
    page.get(sign_in_url)
    if not page.wait_for_page_to_load():
        return False
    if not page.login(email, password):
        return False
    return True

@app.get('/')
async def oauth2_callback(code):
    global callback_value
    global transactions
    callback_value = code
    transactions["pending"] = gettransactionid()
    return JSONResponse({"value": True if callback_value else False}, 200)

@app.get('/renew')
async def renew_token(alias, tenant, saas, bgt: BackgroundTasks):
    global callback_value
    global transactions
    email, password = getemailaddressandpassword(alias=alias, tenant=tenant, saas=saas)
    transactions['pending'].setdefault(email, gettransactionid())
    bgt.add_task(renew_task, email, password)
    bgt.add_task(update_user_token_routine, email)
    return JSONResponse(content={
        "Status": "In Progress",
        "Timestamp": gettimestamp(),
        "TransactionId": transactions['pending'][email],
        "Message": f"use GET /check?transId={transactions['pending'][email]} to verify token storage"
    }, status_code=200)

@app.get('/check')
async def check_transaction(transId):
    global transactions
    if transId in transactions["pending"].values():
        email = [user for user, trans_id in transactions["pending"].items() if transId == trans_id]
        return JSONResponse(content={
            "Status": "In Progress",
            "Timestamp": gettimestamp(),
            "TransactionId": transId,
            "Message": f"task for user={email} is not complete, use GET /check?transId={transId} to verify token storage"
        }, status_code=200)
    elif transId in transactions["done"].values():
        email = [user for user, trans_id in transactions["done"].items() if transId == trans_id]
        return JSONResponse(content={
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "TransactionId": transId,
            "Message": f"task for user={email} is complete, token is stored"
        }, status_code=200)


if __name__ == '__main__':
    run(app, host='0.0.0.0', port=6061)
