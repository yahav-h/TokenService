import os
import pickle
import threading
import time
import helpers
import database
from werkzeug.serving import make_server
from datatypes import TokenUserRecords
from flask import Flask, request, g
from flask.logging import create_logger
from requests_oauthlib import OAuth2Session
from mso_login_page import MSOLoginPage


app = Flask(__name__)
logger = create_logger(app)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'

state = None
oauth2_props = helpers.getoauth2properties()
app_id = oauth2_props['app_id']
scopes = oauth2_props['app_scopes']
redirect = oauth2_props['redirect_uri']
authorize_url = oauth2_props['authorize_url']
app_secret = oauth2_props['app_sec']
token_url = oauth2_props['token_url']

transactions = {
    "pending": {},
    "done": {}
}

def store_token(request, token):
    global transactions
    email = [email for email in transactions['pending'].keys()][0]
    record = TokenUserRecords.query.filter_by(user=email).first()
    if record:
        record.token = pickle.dumps(token)
        database.db_session.add(record)
    else:
        new_record = TokenUserRecords(user=email, token=token)
        database.db_session.add(new_record)
    database.db_session.commit()


def get_sign_in_url():
    aad_auth = OAuth2Session(app_id, scope=scopes, redirect_uri=redirect)
    sign_in_url, state = aad_auth.authorization_url(authorize_url, prompt='login')
    return sign_in_url, state


def get_token_from_code(callback_url, expected_state):
    global transactions
    email = [email for email in transactions['pending'].keys()][0]
    record = TokenUserRecords.query.filter_by(user=email).first()
    token = record.token
    if token:
        now = time.time()
        expire_time = token['expires_at'] - 300
        if now >= expire_time:
            aad_auth = OAuth2Session(app_id, token=token)
            refresh_params = {'client_id': app_id, 'client_secret': app_secret}
            new_token = aad_auth.refresh_token(token_url, **refresh_params)
            store_token(request, new_token)
            return new_token
        else:
            return token
    aad_auth = OAuth2Session(app_id, state=expected_state, scope=scopes, redirect_uri=redirect)
    token = aad_auth.fetch_token(token_url, client_secret=app_secret, code=request.args['code'])
    return token


@app.before_request
def open_db_connection():
    if not database.db_session.registry.has():
        database.db_session = database.scoped_session(
            database.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=database.engine
            )
        )
    app.app_context().push()

@app.after_request
def close_db_connection():
    database.db_session.remove()

@app.route("/", methods=["GET"])
def oauth2_callback():
    global state
    token = get_token_from_code(request.url, state)
    store_token(request, token)
    return {}

@app.route("/renew", methods=["GET"])
def renew_token():
    global state, transactions
    alias = request.args.get("alias")
    tenant = request.args.get("tenant")
    saas = request.args.get("saas")
    email, password = helpers.getemailaddressandpassword(alias, tenant, saas)
    transactions['pending'].setdefault(email, helpers.gettransactionid())
    sign_in_url, state = get_sign_in_url()
    driver = helpers.getwebdriver()
    page = MSOLoginPage(driver, logger)
    page.get(sign_in_url)
    page.wait_for_page_to_load()
    page.login(email, password)
    logger.info(page.get_current_url())
    page.quit()
    return {
        "Status": "In Progress",
        "Timestamp": helpers.gettimestamp(),
        "TransactionId": transactions['pending'][email],
        "Message": f"use GET /check?transId={transactions['pending'][email]} to verify token storage"
    }


if __name__ == '__main__':
    class ThreadServer(threading.Thread):
        def __init__(self, app):
            threading.Thread.__init__(self)
            self.srv = make_server('0.0.0.0', 5000, app)
            self.ctx = app.app_context()
            self.ctx.push()
    server = ThreadServer(app)
    server.ctx.app.run(host="0.0.0.0", port=41197)

