# Token Service Gateway

---
```text

This repository contains a Web Service Application
which allows a requester to CREATE, UPDATE and READ user data by which is used
to gain access into SAAS applications .
   
```
---

## Deploy as a Docker

1. Get the project
```shell
$ git clone https://guthub.com/yahav-h/TokenService.git 
```

2. Update the environment variables at `docker-compose.yml` 
```yaml
version: '3.3'
services:
  token-service:
    build: .
    command: uvicorn token_service_main:app --host 0.0.0.0
    ports:
      - "80:8000"
    environment:
      OAUTH_O365_IP: <IP_ADDRESS>
      OAUTH_GOOG_IP: <IP_ADDRESS>
```
3. Build a new image
```shell
$ docker build -t compose-token-service-gw-fapi .
```
4. Deploy your container
```shell
$ docker-compose up
```
---
## Deploy as a Web Server

1. Get the project
```shell
$ git clone https://guthub.com/yahav-h/TokenService.git 
```
2. Install environment 
```shell
$ /usr/bin/python3 -m venv venv3
$ chmod +x ./start_service.sh
$ chmod +x ./stop_service.sh
```
3. Start / Stop web service
```shell
# start
$ sudo ./start_service.sh
# stop
$ sudo ./stop_service.sh
```


---
## Architecture

![erd-flow](erd-flow.png)