"""Order processor — production source (sprint-3 committed)."""
from __future__ import annotations
import logging
import httpx
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

logger = logging.getLogger(__name__)

COSMOS_URL = "https://myaccount.documents.azure.com:443/"
PAYMENT_GATEWAY_URL = "https://payments.internal/v1/charge"
PAYMENT_TIMEOUT_SECONDS = 5


def _call_payment_gateway(cart: dict) -> tuple[str, str] | None:
    """Call external payment gateway. Returns (order_id, status) or None on error."""
    try:
        resp = httpx.post(
            PAYMENT_GATEWAY_URL,
            json={"amount": cart["total"], "currency": "USD", "card_token": cart["token"]},
            timeout=PAYMENT_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["order_id"], data["status"]
    except httpx.TimeoutException:
        logger.error("Payment gateway timed out for cart %s", cart.get("id"))
        return None  # <-- BUG: caller doesn't handle None return
    except httpx.HTTPStatusError as e:
        logger.error("Payment gateway error: %s", e)
        return None


def process_order(cart: dict) -> dict:
    """Process a customer order end-to-end."""
    credential = DefaultAzureCredential()
    client = CosmosClient(COSMOS_URL, credential=credential)
    db = client.get_database_client("orders")
    container = db.get_container_client("transactions")

    # Validate cart
    if not cart.get("token") or not cart.get("total"):
        raise ValueError("Cart missing required fields: token, total")

    # line 87: unpack — crashes when _call_payment_gateway returns None
    order_id, status = _call_payment_gateway(cart)

    # Persist to Cosmos
    container.upsert_item({
        "id": order_id,
        "cart_id": cart["id"],
        "status": status,
        "amount": cart["total"],
    })

    return {"order_id": order_id, "status": status}
