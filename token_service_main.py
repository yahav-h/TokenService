from fastapi import FastAPI
from fastapi.background import BackgroundTasks
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette_context import context, plugins
from starlette_context.middleware import ContextMiddleware
from logging import getLogger, basicConfig, DEBUG
from requests_oauthlib import OAuth2Session
from time import time
import helpers
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
    filename='%s/runtime.log' % getlogfile()
)
logger = getLogger('ServiceLoger')

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'


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

def update_user_token_routine(token):
    global transactions
    email = [email for email in transactions['pending'].keys()][0]
    logger.info('received EMAIL : %s' % email)
    logger.info('received TOKEN : %s' % token)
    logger.debug('transactions = %r' % transactions)
    try:
        optional: TokenUserRecords = TokenUserRecords.query.filter_by(user=email).first()
        if not optional:
            logger.info('Record not found by %s' % email)
            record = TokenUserRecords(user=email, token=pickle.dumps(token))
            logger.info('Create New Record : %r' % record)
        else:
            logger.info('Record found by %s' % email)
            record = optional
            record.token = pickle.dumps(token)
            logger.info('Updating Record Token : %s' % record.token)
        db_session.add(record)
        db_session.commit()
        logger.info('Record Committed : %r' % record.__dict__)
        transactions["done"][email] = transactions["pending"].pop(email)
        logger.debug('Transactions Updated : %r' % transactions["done"][email])
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
    url = page.get_current_url()
    logger.info("CURRENT URL IS : %s" % url)
    return True


@app.get('/users')
async def get_record_by_email(email: str):
    optional = TokenUserRecords.query.filter_by(user=email).first()
    if not optional:
        return JSONResponse(content={
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {},
            "Message": f"User email {email} does not exists!"
        }, status_code=404)
    else:
        record = optional
        return JSONResponse(content={
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {
                "id": record.id,
                "user": record.user,
                "token": pickle.loads(record.token)
            },
            "Message": f"User email {email} found!"
        }, status_code=200)


@app.get('/records')
async def get_record_by_id(uid: int):
    optional = TokenUserRecords.query.filter_by(id=uid).first()
    if not optional:
        return JSONResponse(content={
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {},
            "Message": f"User ID {uid} does not exists!"
        }, status_code=200)
    else:
        record = optional
        return JSONResponse(content={
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {
                "id": record.id,
                "user": record.user,
                "token": pickle.loads(record.token)
            },
            "Message": f"User ID {uid} found!"
        }, status_code=200)


if __name__ == '__main__':
    run(app, host='0.0.0.0', port=41197)
