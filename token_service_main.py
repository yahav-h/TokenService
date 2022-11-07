from fastapi import FastAPI
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from time import time
from helpers import get_timestamp, get_uuid, request_user_gsuite_token_refresh, request_user_o365_token_refresh, \
    request_user_o365_token, request_user_gsuite_token, request_create_gsuite_token, request_create_o365_token, \
    generic_argument_check, delegate_action, sanitize, logger
from uvicorn import run


app = FastAPI()

@app.middleware('http')
async def add_process_time_header(req: Request, call_next):
    start_time = time()
    res: Response = await call_next(req)
    res.headers.setdefault('x-process-time', f'{time() - start_time}')
    return res


@app.middleware('http')
async def add_response_id_header(req: Request, call_next):
    response_id = get_uuid(time().hex())
    res: Response = await call_next(req)
    res.headers.setdefault('x-response-id', f'{response_id}')
    return res


@app.middleware('http')
async def add_requester_id_header(req: Request, call_next):
    requester_id = get_uuid(req.url.hostname)
    res: Response = await call_next(req)
    res.headers.setdefault('x-requester-id', f'{requester_id}')
    return res

@app.get("/v2/renew")
async def delegate_user_token_refresh(saas, email):
    logger.info("delegate_user_token_refresh (params: %s , %s)" % (saas, email))
    if not generic_argument_check(saas, email):
        logger.warning("generic_argument_check (params: %s , %s) , return False" % (saas, email))
        return JSONResponse({"Status": "Done", "Timestamp": get_timestamp(), "Message": "Missing Email"}, 400)
    if saas == "office365":
        user_data = await delegate_action(request_user_o365_token_refresh, email)
        logger.info("delegate_action (params: %s , %s) , return %r" % (saas, email, user_data))
        return JSONResponse({"Status": "Done", "Timestamp": get_timestamp(), "User": user_data}, 200)
    if saas == "gsuite":
        user_data = await delegate_action(request_user_gsuite_token_refresh, email)
        logger.info("delegate_action (params: %s , %s) , return %r" % (saas, email, user_data))
        return JSONResponse({"Status": "Done", "Timestamp": get_timestamp(), "User": user_data}, 200)

@app.get("/v2/users")
async def delegate_get_user_data(saas, email):
    logger.info("delegate_get_user_data (params: %s , %s)" % (saas, email))
    if not generic_argument_check(saas, email):
        logger.warning("generic_argument_check (params: %s , %s) , return False" % (saas, email))
        return JSONResponse({"Status": "Done", "Timestamp": get_timestamp(), "Message": "Missing Email"}, 400)
    if saas == "office365":
        user_data = await delegate_action(request_user_o365_token, email)
        logger.info("delegate_action (params: %s , %s) , return %r" % (saas, email, user_data))
        return JSONResponse({"Status": "Done", "Timestamp": get_timestamp(), "User": user_data}, 200)
    if saas == "gsuite":
        user_data = await delegate_action(request_user_gsuite_token, email)
        logger.info("delegate_action (params: %s , %s) , return %r" % (saas, email, user_data))
        return JSONResponse({"Status": "Done", "Timestamp": get_timestamp(), "User": user_data}, 200)


@app.post("/v2/createToken")
async def delegate_create_token(saas, email):
    logger.info("delegate_create_token (params: %s , %s)" % (saas, email))
    if not generic_argument_check(saas, email):
        logger.warning("generic_argument_check (params: %s , %s) , return False" % (saas, email))
        return JSONResponse({"Status": "Done", "Timestamp": get_timestamp(), "Message": "Missing Email"}, 400)
    if saas == "office365":
        user_data = await delegate_action(request_create_o365_token, email)
        logger.info("delegate_action (params: %s , %s) , return %r" % (saas, email, user_data))
        context, status_code = sanitize(user_data, email)
        logger.info("sanitize (params: %s , %s) , return (%s, %s)" % (user_data, email, context, status_code))
        return JSONResponse({"Status": "Done", "Timestamp": get_timestamp(), "Response": context}, status_code)
    if saas == "gsuite":
        user_data = await delegate_action(request_create_gsuite_token, email)
        logger.info("delegate_action (params: %s , %s) , return %r" % (saas, email, user_data))
        context, status_code = sanitize(user_data, email)
        logger.info("sanitize (params: %s , %s) , return (%s, %s)" % (user_data, email, context, status_code))
        return JSONResponse({"Status": "Done", "Timestamp": get_timestamp(), "Response": context}, status_code)


if __name__ == '__main__':
    run(app, host="0.0.0.0", port=80)
