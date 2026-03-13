---
name: azure-communication-services
description: >
  Azure Communication Services SDK for Python. Use for sending emails, SMS messages,
  and managing communication identities. Triggers on: "azure communication services",
  "EmailClient", "SmsClient", "CommunicationIdentityClient", "send email", "send SMS",
  "communication identity", "ACS", "begin_send", "access token". CRITICAL: Email uses
  begin_send() (LRO poller), not send(). SMS from_ parameter has underscore.
---

# Azure Communication Services SDK for Python

## Packages
```bash
pip install azure-communication-email        # Email
pip install azure-communication-sms          # SMS
pip install azure-communication-identity     # Identity/tokens
pip install azure-identity
```

## Email — EmailClient

```python
from azure.communication.email import EmailClient
from azure.identity import DefaultAzureCredential

# Connection string auth (dev)
client = EmailClient.from_connection_string("endpoint=https://...;accesskey=...")

# AAD auth (production)
client = EmailClient(
    endpoint="https://myresource.communication.azure.com",
    credential=DefaultAzureCredential(),
)
```

### Send email (`begin_send` — returns LRO poller)

```python
message = {
    "senderAddress": "donotreply@mydomain.azurecomm.net",
    "recipients": {
        "to": [{"address": "user@example.com", "displayName": "User Name"}],
        "cc": [],
        "bcc": [],
    },
    "content": {
        "subject": "Hello from ACS",
        "plainText": "Hello World",
        "html": "<html><body><h1>Hello World</h1></body></html>",
    },
    "attachments": [
        {
            "name": "report.pdf",
            "contentType": "application/pdf",
            "contentInBase64": base64_encoded_string,
        }
    ],
}

# begin_send() returns an LRO poller — MUST call .result() or poll
poller = client.begin_send(message)
result = poller.result()   # blocks until done

print(result.id)            # message ID
print(result.status)        # "Succeeded", "Failed", etc.
```

### Poll without blocking

```python
poller = client.begin_send(message)

# Check status without blocking
while not poller.done():
    status = poller.status()   # "Running", "Succeeded", "Failed"
    time.sleep(5)

result = poller.result()
```

## SMS — SmsClient

```python
from azure.communication.sms import SmsClient

client = SmsClient.from_connection_string("endpoint=...;accesskey=...")
# or AAD: SmsClient(endpoint=..., credential=DefaultAzureCredential())
```

### Send SMS

```python
# from_ uses underscore (avoids Python keyword `from`)
results = client.send(
    from_="+15551234567",          # ACS phone number you purchased
    to=["+15559876543"],           # always a list, even single recipient
    message="Hello from ACS",
    enable_delivery_report=True,   # optional
)

# Returns List[SmsSendResult] — always a list
for result in results:
    print(result.to)               # recipient number
    print(result.message_id)       # tracking ID
    print(result.successful)       # bool
    if not result.successful:
        print(result.http_status_code, result.error_message)
```

## Identity — CommunicationIdentityClient

```python
from azure.communication.identity import (
    CommunicationIdentityClient,
    CommunicationTokenScope,
)

client = CommunicationIdentityClient.from_connection_string("...")
```

### Create user and issue token

```python
# Create a user
user = client.create_user()
user_id = user.properties["id"]    # Access via dict, NOT .id

# Issue an access token
token_result = client.get_token(
    user,
    scopes=[CommunicationTokenScope.VOIP, CommunicationTokenScope.CHAT],
)
print(token_result.token)          # JWT token string
print(token_result.expires_on)     # datetime

# Create user + token in one call
user, token_result = client.create_user_and_token(
    scopes=[CommunicationTokenScope.CHAT]
)

# Refresh token
refreshed = client.get_token(user, scopes=[CommunicationTokenScope.CHAT])

# Revoke all tokens for a user
client.revoke_tokens(user)

# Delete user permanently
client.delete_user(user)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `client.send(message)` (email) | `client.begin_send(message)` — returns LRO poller |
| Ignoring `.result()` on poller | `result = poller.result()` to get final status |
| `from="..."` in SMS | `from_="..."` — underscore avoids Python keyword |
| `client.send(from_=..., to="+1...")` SMS to string | `to=["+1..."]` — must be a list |
| `result.to` on SMS expecting single string | Always a list result, iterate it |
| `user.id` on identity user | `user.properties["id"]` — it's a dict key |
| Single scope: `scopes=CommunicationTokenScope.CHAT` | `scopes=[CommunicationTokenScope.CHAT]` — list |
