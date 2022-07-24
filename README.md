# TokenService

---
```text
This repository contains a saas that renew tokens for mailboxes in the cloud (at the moment supporting Office365 Outlook) 
```

### Overview 
TokenService goal is to refresh oauth2 token access to an account of the Microsoft Office 365 Suite .

The service will attempt to refresh a token and then store it in a database for future usage.

The service store authorization tokens which then can be used for future purpose using a GET request 

---

### HOW TO:

1. give permission to the startservice script
```shell    
$ chmod 777 ./start_service.sh
```
2. edit the port to your relevant port
```shell
$ cat ./token_service_main.py | sed s/port="41197"/port="...."/g  
```
3. edit to your matching table name in your db
```shell
$ cat ./dao.py | sed s/__tablename__="token_user_records"/__tablename__="...."/g
```
4. update your template properties with your relevant values

--- 
### Flow
![erd flow](erd-flow.png)