---
name: azure-notification-hubs
description: >
  Azure Notification Hubs for Python — push notification management via management SDK
  and REST API. Use for registering devices, sending push notifications to iOS (APNS),
  Android (FCM/GCM), and Windows (WNS), and tag-based targeting. Triggers on:
  "notification hubs", "NotificationHubsClient", "push notifications", "APNS", "FCM",
  "WNS", "device registration", "tag expressions", "SAS token notification".
  NOTE: No built-in send method — must use REST API with SAS token.
---

# Azure Notification Hubs for Python

## Packages
```bash
pip install azure-mgmt-notificationhubs   # Management (create/configure hubs)
pip install azure-identity
pip install requests                       # For REST API sends
```

> **Key fact:** The Python SDK manages hub infrastructure but has no built-in
> notification send method. Sending requires calling the REST API directly with
> a generated SAS token.

## Management — create/configure hubs

```python
from azure.mgmt.notificationhubs import NotificationHubsManagementClient
from azure.identity import DefaultAzureCredential

client = NotificationHubsManagementClient(
    credential=DefaultAzureCredential(),
    subscription_id="your-subscription-id",
)

# List namespaces
for ns in client.namespaces.list():
    print(ns.name, ns.location)

# Create hub
hub = client.notification_hubs.create_or_update(
    resource_group_name="myRG",
    namespace_name="myNamespace",
    notification_hub_name="myHub",
    parameters={
        "location": "eastus",
        "properties": {
            "apns_credential": {
                "properties": {
                    "key_id": "KEY_ID",
                    "app_name": "MyApp",
                    "app_id": "TEAM_ID",
                    "token": "APNs_auth_token",
                    "endpoint": "https://api.push.apple.com/",
                }
            }
        },
    },
)
```

## SAS token generation (required for REST sends)

```python
import hmac, hashlib, base64, urllib.parse, time

def generate_sas_token(uri: str, key_name: str, key_value: str, ttl_seconds: int = 3600) -> str:
    """Generate SAS token for Notification Hubs REST API."""
    expiry = int(time.time()) + ttl_seconds
    string_to_sign = urllib.parse.quote_plus(uri) + "\n" + str(expiry)
    signature = base64.b64encode(
        hmac.new(
            key_value.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")
    return (
        f"SharedAccessSignature sr={urllib.parse.quote_plus(uri)}"
        f"&sig={urllib.parse.quote_plus(signature)}"
        f"&se={expiry}&skn={key_name}"
    )
```

## Sending notifications via REST API

```python
import requests

NAMESPACE = "myNamespace"
HUB_NAME  = "myHub"
KEY_NAME  = "DefaultFullSharedAccessSignature"
KEY_VALUE = "your-sas-key-value"

base_url = f"https://{NAMESPACE}.servicebus.windows.net/{HUB_NAME}"
sas_token = generate_sas_token(base_url, KEY_NAME, KEY_VALUE)

headers = {
    "Authorization": sas_token,
    "Content-Type": "application/json;charset=utf-8",
    "ServiceBusNotification-Format": "apple",   # "apple", "gcm", "windows", "template"
}

# iOS (APNS) payload
apns_payload = '{"aps":{"alert":"Hello from Azure!","badge":1}}'

# Android (FCM v1) payload
fcm_payload = '{"message":{"notification":{"title":"Hello","body":"From Azure"}}}'

# Tag-based send (target specific users)
headers["ServiceBusNotification-Tags"] = "user-123 || premium-user"

response = requests.post(
    f"{base_url}/messages/?api-version=2015-01",
    headers=headers,
    data=apns_payload.encode("utf-8"),
)
print(response.status_code)   # 201 = accepted
```

## Template notifications (cross-platform)

```python
# Template notification — uses registered templates on devices
headers["ServiceBusNotification-Format"] = "template"
template_payload = '{"message":"Hello World","badge":"5"}'   # matches template variables

response = requests.post(
    f"{base_url}/messages/?api-version=2015-01",
    headers=headers,
    data=template_payload.encode("utf-8"),
)
```

## Platform payload formats

```python
# iOS (APNS)
apns = '{"aps":{"alert":"msg","badge":1,"sound":"default"},"custom":"data"}'

# Android (FCM legacy)
fcm_legacy = '{"data":{"title":"msg","body":"text"},"notification":{"title":"msg"}}'

# Android (FCM v1 — recommended)
fcm_v1 = '{"message":{"notification":{"title":"Title","body":"Body"}}}'

# Windows (WNS — XML toast)
wns_toast = """<toast><visual><binding template="ToastText01">
<text id="1">Hello from Azure</text></binding></visual></toast>"""

# For WNS, also set X-WNS-Type header:
headers["X-WNS-Type"] = "wns/toast"
headers["Content-Type"] = "text/xml"
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| Calling `client.send_notification()` on mgmt client | No built-in send — use REST API |
| Forgetting SAS token on REST call | Every REST request needs `Authorization: SharedAccessSignature ...` |
| Missing `ServiceBusNotification-Format` header | Required — set to `"apple"`, `"gcm"`, `"windows"`, or `"template"` |
| Sending FCM legacy payload to FCM v1 endpoint | Use v1 format `{"message":{...}}` for modern FCM |
| Sending to `/messages` without `api-version` | Add `?api-version=2015-01` to URL |
