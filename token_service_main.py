import base64
from fastapi import FastAPI
from fastapi.background import BackgroundTasks
from pydantic import BaseModel
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette_context import plugins
from starlette_context.middleware import ContextMiddleware
from requests_oauthlib import OAuth2Session
from time import time
from pages.mso_login_page import MSOLoginPage
from pages.goog_login_page import GoogLoginPage
from helpers import getoauth2properties, getwebdriver, getemailaddressandpassword, \
    gettransactionid, gettimestamp, getuuidx, extract_params
from dao import TokenUserRecordsDAO
from dto import TokenUserRecordsDTO
from database import get_session, localdb, Base, engine
import google_auth_oauthlib
from uvicorn import run
import pickle
import os


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


class OAuth2Jwt(BaseModel):
    data: str
    def pklloads(self): return pickle.loads(base64.b64decode(self.data))


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
    return res


@app.middleware('http')
async def add_requester_id_header(req: Request, call_next):
    requester_id = getuuidx(req.url.hostname)
    res: Response = await call_next(req)
    res.headers.setdefault('x-requester-id', f'{requester_id}')
    return res


def update_user_token_routine(token):
    global transactions
    email = [email for email in transactions['pending'].keys()][0]
    print('received EMAIL : %s' % email)
    print('received TOKEN : %s' % token)
    print('transactions = %r' % transactions)
    try:
        dao = TokenUserRecordsDAO.query.filter_by(user=email).first()
        if not dao:
            print('Record not found by %s' % email)
            dao = TokenUserRecordsDAO(user=email, token=pickle.dumps(token))
        else:
            print('Record found by %s' % email)
            dao.token = pickle.dumps(token)
        with get_session() as Session:
            Session.add(dao)
        transactions["done"][email] = transactions["pending"].pop(email)
        print('Transactions Updated : %r' % transactions["done"][email])
        return True
    except Exception as e:
        print('Something Went Wrong')
        print(e)
        return False


def base_scrapes_oauth_2_any_saas(page, sign_in_url, CREDENTIAL_OBJECT):
    try:
        page.get(sign_in_url)
        if page.wait_for_page_to_load():
            url = page.login(CREDENTIAL_OBJECT['email'], CREDENTIAL_OBJECT['password'])
            print("CURRENT URL IS : %s" % url)
            return url
    finally:
        page.cleanup()


def selenium_scraps_oauth_2_googleapis(page, SAAS_OBJECT, CREDENTIAL_OBJECT):
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {'web': SAAS_OBJECT['web']},
        scopes=SAAS_OBJECT['app_scopes']
    )
    flow.redirect_uri = SAAS_OBJECT['web']['redirect_uris'][0]
    sign_in_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    url = base_scrapes_oauth_2_any_saas(page, sign_in_url, CREDENTIAL_OBJECT)
    code, state, scopes = extract_params(url)
    token = flow.fetch_token(code=code)
    update_user_token_routine(token=token)


def selenium_scraps_oauth_2_office365(page, SAAS_OBJECT, CREDENTIAL_OBJECT):
    aad_auth = OAuth2Session(SAAS_OBJECT["app_id"], scope=SAAS_OBJECT["app_scopes"],
                             redirect_uri=SAAS_OBJECT["redirect_uri"])
    sign_in_url, state = aad_auth.authorization_url(SAAS_OBJECT["authorize_url"], prompt='login')
    url = base_scrapes_oauth_2_any_saas(page, sign_in_url, CREDENTIAL_OBJECT)
    print(f"GOT URL : {url}")


def renew_task(saas, email, password):
    print("Start task for SAAS : %s " % saas)
    print('Will use : %s:%s' % (email, password))
    creds = {'email': email, 'password': password}
    props = getoauth2properties()
    driver = getwebdriver()
    if saas == 'office365':
        page = MSOLoginPage(driver)
        selenium_scraps_oauth_2_office365(page, props[saas], creds)
    elif saas == 'gsuite':
        page = GoogLoginPage(driver)
        selenium_scraps_oauth_2_googleapis(page, props[saas], creds)


@app.get('/')
async def oauth2_callback_office365(code, state, session_state):
    print("oauth2 callback params : %r" % [code, state, session_state])
    dao = TokenUserRecordsDAO.query.filter_by(user=...).first()
    if not dao:
        not_exist_content = {

        }
        return JSONResponse(content=not_exist_content, status_code=200)
    dto = TokenUserRecordsDTO(
        id=dao.id,
        user=dao.user,
        token=dao.token
    )
    token = pickle.dumps(dto.token)
    props = getoauth2properties()
    now = time()
    expire_time = token["expires_at"] - 300
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
    print('received : %s, %s, %s' % (alias, tenant, saas))
    global transactions
    print('transactions = %r' % transactions)
    email, password = getemailaddressandpassword(alias=alias, tenant=tenant, saas=saas)
    transactions['pending'].setdefault(email, gettransactionid())
    print('Updating Transactions : %r' % transactions)
    bgt.add_task(renew_task, saas, email, password)
    content = {
        "Status": "In Progress",
        "Timestamp": gettimestamp(),
        "TransactionId": transactions['pending'][email],
        "Message": f"use GET /check?transId={transactions['pending'][email]} to verify token storage"
    }
    print(f'renew_token | {content}')
    return JSONResponse(content=content, status_code=200)


@app.get('/check')
async def check_transaction(transId):
    global transactions
    print('transactions = %r' % transactions)
    for k, v in transactions["pending"].items():
        if transId != v:
            continue
        else:
            email = k
            print("Transactions is still PENDING")
            content = {
                "Status": "In Progress",
                "Timestamp": gettimestamp(),
                "TransactionId": transId,
                "Token": None,
                "Message": f"task for user={email} is not complete, use GET /check?transId={transId} to verify token storage"
            }
            print(f"check_transaction | {content}")
            return JSONResponse(content=content, status_code=200)
    for k, v in transactions["done"].items():
        if transId != v:
            continue
        else:
            email = k
            record = TokenUserRecordsDAO.query.filter_by(user=email).first()
            print("Transactions is COMPLETED")
            transactions["done"].pop(email)
            content = {
                "Status": "Done",
                "Timestamp": gettimestamp(),
                "TransactionId": transId,
                "Token": pickle.loads(record.token),
                "Message": f"task for user={email} is complete, token is stored"
            }
            print(f"check_transaction | {content}")
            return JSONResponse(content=content, status_code=200)


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
            print(f"get_record_by_email | {not_exists_content}")
            return JSONResponse(content=not_exists_content, status_code=200)
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
            print(f"get_record_by_email | {content}")
            return JSONResponse(content=content, status_code=200)
    except Exception as e:
        err_content = {
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {},
            "Message": "Failed to fetch and / or access data from database"
        }
        print(f"get_record_by_email | {err_content}")
        print(e)
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
            print(f"get_record_by_id | {not_exist_content}")
            return JSONResponse(content=not_exist_content, status_code=200)
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
            print(f"get_record_by_id | {content}")
            return JSONResponse(content=content, status_code=200)
    except Exception as e:
        err_content = {
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {},
            "Message": "Failed to fetch and / or access data from database"
        }
        print(f"get_record_by_id | {err_content}")
        print(e)
        return JSONResponse(content=err_content, status_code=404)


@app.post('/users')
async def add_or_update_user_record_by_email(email: str, oauth: OAuth2Jwt):
    try:
        print(f"email : {email} | oauth : {oauth}")
        data = oauth.pklloads()
        pkl_data = pickle.dumps(data)
        dao = TokenUserRecordsDAO.query.filter_by(user=email).first()
        if not dao:
            dao = TokenUserRecordsDAO(user=email, token=pkl_data)
        dao.token = pkl_data
        new_content = {
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {
                "id": dao.id,
                "user": dao.user,
                "token": pickle.loads(dao.token)
            },
            "Message": f"User email {email} updated!"
        }
        with get_session() as Session:
            Session.add(dao)
        print(f"add_or_update_user_record_by_email | {new_content}")
        return JSONResponse(content=new_content, status_code=200)
    except Exception as e:
        err_content = {
            "Status": "Done",
            "Timestamp": gettimestamp(),
            "User": {},
            "Message": f"Failed to add and / or update data for user {email}"
        }
        print(f"add_or_update_user_record_by_email | {err_content}")
        print(e)
        return JSONResponse(content=err_content, status_code=404)

if __name__ == '__main__':
    if localdb:
        Base.metadata.create_all(bind=engine)
    run(app, host='0.0.0.0', port=41197)
