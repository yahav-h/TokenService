from fastapi import FastAPI
from fastapi.background import BackgroundTasks
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette_context import context, plugins
from starlette_context.middleware import ContextMiddleware
from logging import getLogger, basicConfig, DEBUG
from requests_oauthlib import OAuth2Session
from mso_login_page import MSOLoginPage
from helpers import getoauth2properties, getwebdriver, getemailaddressandpassword, \
    gettransactionid, gettimestamp, getlogfile
from datatypes import TokenUserRecords
from database import db_session
from uvicorn import run
import pickle
import os

FORMAT = '%(thread)d | %(levelname)s | %(asctime)s | %(filename)s | %(module)s::%(funcName)s | %(message)s'
basicConfig(
    filemode='w',
    format=FORMAT,
    level=DEBUG,
    filename='%s/runtime-%s.log' % (getlogfile(), gettimestamp())
)
logger = getLogger('ServiceLoger')

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
    logger.info('received : %s' % email)
    global callback_value
    logger.debug('callback_value = %s' % callback_value)
    global transactions
    logger.debug('transactions = %r' % transactions)
    try:
        optional: TokenUserRecords = TokenUserRecords.query.filter_by(user=email).first()
        if not optional:
            logger.info('Record not found by %s' % email)
            record = TokenUserRecords(user=email, token=callback_value)
            logger.info('Create New Record : %r' % record)
        else:
            logger.info('Record found by %s' % email)
            record = optional
            record.token = pickle.dumps(callback_value)
            logger.info('Updating Record Token : %s' % record.token)
        db_session.add(record)
        db_session.commit()
        logger.info('Record Committed : %r' % record)
        transactions["done"][email] = transactions["pending"].pop(email)
        logger.debug('Transactions Updated : %r' % transactions["done"][email])
        callback_value = None
        logger.debug('callback_value is now : %s' % callback_value)
        return True
    except Exception as e:
        logger.warning('Something Went Wrong')
        logger.error(e)
        return False

def renew_task(email, password):
    logger.info('received : %s:%s' % (email, password))
    props = getoauth2properties()
    aad_auth = OAuth2Session(props["app_id"], scope=props["app_scopes"], redirect_uri=props["redirect_uri"])
    sign_in_url, state = aad_auth.authorization_url(props["authorize_url"], prompt='login')
    webdriver = getwebdriver()
    page = MSOLoginPage(webdriver, logger=logger)
    page.get(sign_in_url)
    if not page.wait_for_page_to_load():
        return False
    if not page.login(email, password):
        return False
    return True

@app.get('/')
async def oauth2_callback(code):
    logger.info('received : %s' % code)
    global callback_value
    logger.debug('callback_value = %s' % callback_value)
    global transactions
    logger.debug('transactions = %r' % transactions)
    callback_value = code
    transactions["pending"] = gettransactionid()
    logger.debug('Updating Transactions : %r' % transactions)
    return JSONResponse({"value": True if callback_value else False}, 200)

@app.get('/renew')
async def renew_token(alias, tenant, saas, bgt: BackgroundTasks):
    logger.info('received : %s, %s, %s' % (alias, tenant, saas))
    global callback_value
    logger.debug('callback_value = %s' % callback_value)
    global transactions
    logger.debug('transactions = %r' % transactions)
    email, password = getemailaddressandpassword(alias=alias, tenant=tenant, saas=saas)
    transactions['pending'].setdefault(email, gettransactionid())
    logger.debug('Updating Transactions : %r' % transactions)
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
    logger.debug('transactions = %r' % transactions)
    if transId in transactions["pending"].values():
        email = [user for user, trans_id in transactions["pending"].items() if transId == trans_id]
        logger.info("Transactions is still PENDING")
        return JSONResponse(content={
            "Status": "In Progress",
            "Timestamp": gettimestamp(),
            "TransactionId": transId,
            "Token": None,
            "Message": f"task for user={email} is not complete, use GET /check?transId={transId} to verify token storage"
        }, status_code=200)
    elif transId in transactions["done"].values():
        email = [user for user, trans_id in transactions["done"].items() if transId == trans_id]
        record = TokenUserRecords.query.filter_by(user=email).first()
        logger.info("Transactions is COMPLETED")
        return JSONResponse(content={
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "TransactionId": transId,
            "Token": record.token,
            "Message": f"task for user={email} is complete, token is stored"
        }, status_code=200)





if __name__ == '__main__':
    run(app, host='0.0.0.0', port=6061)
