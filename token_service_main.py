from fastapi import FastAPI
from fastapi.background import BackgroundTasks
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette_context import context, plugins
from starlette_context.middleware import ContextMiddleware
from logging import getLogger, DEBUG
from logging.handlers import RotatingFileHandler
from requests_oauthlib import OAuth2Session
from time import time
from mso_login_page import MSOLoginPage
from helpers import getoauth2properties, getwebdriver, getemailaddressandpassword, \
    gettransactionid, gettimestamp, getlogfile, getuuidx
from dao import TokenUserRecordsDAO
from dto import TokenUserRecordsDTO
from database import get_session
from uvicorn import run
import pickle
import os

logger = getLogger('ServiceLogger')
logger.setLevel(DEBUG)
handler = RotatingFileHandler(
    filename='%s/runtime.log' % getlogfile(),
    maxBytes=1024*4,
    backupCount=10
)
logger.addHandler(handler)

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


@app.middleware('http')
async def add_process_time_header(req: Request, call_next):
    start_time = time()
    res: Response = await call_next(req)
    res.headers.setdefault('x-process-time', f'{time() - start_time}')
    return res


@app.middleware('http')
async def add_response_id_header(req: Request, call_next):
    response_id = getuuidx(time().hex())
    res: Response = await call_next(req)
    res.headers.setdefault('x-response-id', f'{response_id}')
    logger.debug(res.headers)
    return res


@app.middleware('http')
async def add_requester_id_header(req: Request, call_next):
    requester_id = getuuidx(req.url.hostname)
    res: Response = await call_next(req)
    res.headers.setdefault('x-requester-id', f'{requester_id}')
    logger.debug(res.headers)
    return res


def update_user_token_routine(token):
    global transactions
    email = [email for email in transactions['pending'].keys()][0]
    logger.info('received EMAIL : %s' % email)
    logger.info('received TOKEN : %s' % token)
    logger.debug('transactions = %r' % transactions)
    try:
        dao = TokenUserRecordsDAO.query.filter_by(user=email).first()
        if not dao:
            logger.info('Record not found by %s' % email)
            record = TokenUserRecordsDAO(user=email, token=pickle.dumps(token))
            logger.info('Create New Record : %r' % record)
        else:
            logger.info('Record found by %s' % email)
            dao.token = pickle.dumps(token)
            logger.info('Updating Record Token : %s' % dao.token)
        with get_session() as Session:
            Session.add(dao)
        logger.info('Record Committed : %r' % dao.__dict__)
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


@app.get('/')
async def oauth2_callback(code, state, session_state):
    logger.info('received CODE : %s' % code)
    logger.info('received STATE : %s' % state)
    logger.info('received SESSION_STATE : %s' % session_state)
    dao = TokenUserRecordsDAO.query.filter_by(user=...).first()
    if not dao:
        not_exist_content = {

        }
        logger.debug(f"DAO : {dao} | RESPONSE : {not_exist_content}")
        return JSONResponse(content=not_exist_content, status_code=201)
    dto = TokenUserRecordsDTO(
        id=dao.id,
        user=dao.user,
        token=dao.token
    )
    token = pickle.dumps(dto.token)
    props = getoauth2properties()
    now = time()
    expire_time = token['expires_at'] - 300
    if now >= expire_time:
        aad_auth = OAuth2Session(props['app_id'], token=token)
        refresh_params = {'client_id': props['app_id'], 'client_secret': props['app_sec']}
        new_token = aad_auth.refresh_token(token_url=props['token_url'], **refresh_params)
        update_user_token_routine(token=new_token)
        return JSONResponse({"value": new_token}, 200)
    else:
        return JSONResponse({"value": token}, 200)


@app.get('/renew')
async def renew_token(alias, tenant, saas, bgt: BackgroundTasks):
    logger.info('received : %s, %s, %s' % (alias, tenant, saas))
    global transactions
    logger.debug('transactions = %r' % transactions)
    email, password = getemailaddressandpassword(alias=alias, tenant=tenant, saas=saas)
    transactions['pending'].setdefault(email, gettransactionid())
    logger.debug('Updating Transactions : %r' % transactions)
    bgt.add_task(renew_task, email, password)
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
    for k, v in transactions["pending"].items():
        if transId != v:
            continue
        else:
            email = k
            logger.info("Transactions is still PENDING")
            return JSONResponse(content={
                "Status": "In Progress",
                "Timestamp": gettimestamp(),
                "TransactionId": transId,
                "Token": None,
                "Message": f"task for user={email} is not complete, use GET /check?transId={transId} to verify token storage"
            }, status_code=200)
    for k, v in transactions["done"].items():
        if transId != v:
            continue
        else:
            email = k
            record = TokenUserRecordsDAO.query.filter_by(user=email).first()
            logger.info("Transactions is COMPLETED")
            return JSONResponse(content={
                "Status": "Done",
                "Timestamp": gettimestamp(),
                "TransactionId": transId,
                "Token": pickle.loads(record.token),
                "Message": f"task for user={email} is complete, token is stored"
            }, status_code=200)


@app.get('/users')
async def get_record_by_email(email: str):
    try:
        dao = TokenUserRecordsDAO.query.filter_by(user=email).first()
        if not dao:
            not_exists_content = {
                "Status": "Done",
                "Timestamp": gettimestamp(),
                "User": {},
                "Message": f"User email {email} does not exists!"
            }
            logger.debug(f"DAO : {dao} | RESPONSE : {not_exists_content}")
            return JSONResponse(content=not_exists_content, status_code=201)
        else:
            dto = TokenUserRecordsDTO(
                id=dao.id,
                user=dao.user,
                token=dao.token
            )
            content = {
                "Status": "Done",
                "Timestamp": gettimestamp(),
                "User": {
                    "id": dto.id,
                    "user": dto.user,
                    "token": pickle.loads(dto.token)
                },
                "Message": f"User email {email} found!"
            }
            logger.debug(f"DTO : {dto} | RESPONSE : {content}")
            return JSONResponse(content=content, status_code=200)
    except Exception as e:
        err_content = {
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {},
            "Message": "Failed to fetch and / or access data from database"
        }
        logger.debug(f"RESPONSE : {err_content}")
        logger.error(e)
        return JSONResponse(content=err_content, status_code=404)


@app.get('/records')
async def get_record_by_id(uid: int):
    try:
        dao = TokenUserRecordsDAO.query.filter_by(id=uid).first()
        if not dao:
            not_exist_content = {
                "Status": "Done",
                "Timestamp": gettimestamp(),
                "User": {},
                "Message": f"User ID {uid} does not exists!"
            }
            logger.debug(f"DAO : {dao} | RESPONSE : {not_exist_content}")
            return JSONResponse(content=not_exist_content, status_code=201)
        else:
            dto = TokenUserRecordsDTO(
                id=dao.id,
                user=dao.user,
                token=dao.token
            )
            content = {
                "Status": "Done",
                "Timestamp": gettimestamp(),
                "User": {
                    "id": dto.id,
                    "user": dto.user,
                    "token": pickle.loads(dto.token)
                },
                "Message": f"User ID {uid} found!"
            }
            logger.debug(f"DTA : {dto} | RESPONSE : {content}")
            return JSONResponse(content=content, status_code=200)
    except Exception as e:
        err_content = {
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {},
            "Message": "Failed to fetch and / or access data from database"
        }
        logger.debug(f"RESPONSE : {err_content}")
        logger.error(e)
        return JSONResponse(content=err_content, status_code=404)


@app.post('/users')
async def get_record_by_id(email: str, req: Request):
    try:
        dao = TokenUserRecordsDAO.query.filter_by(user=email).first()
        if not dao:
            not_exist_content = {
                "Status": "Done",
                "Timestamp": gettimestamp(),
                "User": {},
                "Message": f"User email {email} does not exists!"
            }
            logger.debug(f"DAO : {dao} | RESPONSE : {not_exist_content}")
            return JSONResponse(content=not_exist_content, status_code=201)
        else:
            new_token = await req.json()
            dao.token = pickle.dumps(new_token)
            content = {
                "Status": "Done",
                "Timestamp": gettimestamp(),
                "User": {
                    "id": dao.id,
                    "user": dao.user,
                    "token": pickle.loads(dao.token)
                },
                "Message": f"User email {email} updated!"
            }
            logger.debug(f"DAO : {dao} | RESPONSE : {content}")
            with get_session() as Session:
                Session.add(dao)
            return JSONResponse(content=content, status_code=200)
    except Exception as e:
        err_content = {
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {},
            "Message": "Failed to fetch and / or access data from database"
        }
        logger.debug(f"RESPONSE : {err_content}")
        logger.error(e)
        return JSONResponse(content=err_content, status_code=404)

if __name__ == '__main__':
    run(app, host='0.0.0.0', port=41197)
