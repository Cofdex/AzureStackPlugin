# Bug Report: bugfix-order-processor-crash-001

## Symptom
Order processing crashes in production when the payment processor times out.

**Error:**
```
TypeError: cannot unpack non-iterable NoneType object
  File "src/orders/processor.py", line 87, in process_order
    order_id, status = _call_payment_gateway(cart)
```

**Frequency:** Every order where payment gateway takes > 5s (timeout condition)
**Environment:** Production Azure Container Apps, Python 3.12
**Duration:** 3 hours, ~140 failed orders

## Steps to reproduce
1. Submit an order while the payment gateway is rate-limited or slow
2. `_call_payment_gateway` returns `None` on timeout
3. Line 87 attempts to unpack the `None` return value → crash
