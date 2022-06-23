# TokenService

---
```text
This repository contains a saas that renew tokens for mailboxes in the cloud (at the moment supporting Office365 Outlook) 
```

### Overview 
TokenService goal is to refresh oauth2 token access to an account of the Microsoft Office 365 Suite .

The service will attempt to refresh a token and then store it in a database for future usage.

### Flow
![erd flow](erd-flow.png)