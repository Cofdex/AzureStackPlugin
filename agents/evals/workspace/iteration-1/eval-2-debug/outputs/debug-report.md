# Debug Report: bugfix-order-processor-crash-001

## Bug summary
`process_order` crashes with `TypeError: cannot unpack non-iterable NoneType object` whenever `_call_payment_gateway` returns `None` on a payment gateway timeout or HTTP error.

## Root cause
**File**: `src/orders/processor.py`  
**Function**: `process_order`  
**Line**: 46  
**Explanation**: `_call_payment_gateway` is explicitly documented to return `tuple[str, str] | None` — it returns `None` on `TimeoutException` or `HTTPStatusError`. The caller `process_order` unconditionally unpacks the return value on line 46:

```python
order_id, status = _call_payment_gateway(cart)   # line 46
```

When the gateway is slow (> 5 s) or rate-limited, `_call_payment_gateway` returns `None`. Python then raises `TypeError: cannot unpack non-iterable NoneType object` because `None` cannot be destructured into two variables. There is no guard between the call and the unpack.

## Root cause type
`CODE_BUG`

## Reproduction steps
1. Call `process_order({"id": "x", "token": "tok", "total": 10.0})` while `_call_payment_gateway` is patched to return `None` (or while the real gateway is unreachable/slow).
2. Python evaluates `order_id, status = None` → `TypeError` is raised.
3. The exception propagates uncaught out of `process_order`.

## Failing test
- **Path**: `agents/evals/workspace/iteration-1/eval-2-debug/outputs/test_processor.py`
- **Test name**: `test_raises_informative_error_instead_of_type_error` and `test_no_type_error_on_gateway_timeout`
- **Expected**: `process_order` raises `RuntimeError` (or a named `PaymentGatewayError`) with a message that clearly communicates payment failure — never `TypeError`.
- **Actual**: `TypeError: cannot unpack non-iterable NoneType object` is raised from the naked unpack on line 46.
- **Confirmed failing**: YES

Pytest run output:
```
FAILED test_processor.py::TestProcessOrderHandlesPaymentGatewayNone::test_raises_informative_error_instead_of_type_error
  processor.py:46: in process_order
      order_id, status = _call_payment_gateway(cart)
      ^^^^^^^^^^^^^^^^
  TypeError: cannot unpack non-iterable NoneType object
1 failed, 2 passed in 0.39s
```

## Proposed fix
In `process_order`, immediately after calling `_call_payment_gateway`, add a `None` guard before the unpack. If the result is `None`, raise a clear, named exception (e.g. `RuntimeError("Payment gateway unavailable — order not processed")` or a custom `PaymentGatewayError`). Do not silently swallow or retry here — just raise so the caller (API layer / queue consumer) can handle it appropriately.

Concretely, replace:
```python
order_id, status = _call_payment_gateway(cart)
```
with logic equivalent to:
```python
result = _call_payment_gateway(cart)
if result is None:
    raise RuntimeError("Payment gateway unavailable — order not processed for cart %s" % cart.get("id"))
order_id, status = result
```

No changes to `_call_payment_gateway` itself are needed — its return contract is already correct and documented.

## Files likely to change
- `src/orders/processor.py` — add None-guard in `process_order` around line 46

## Side effect risks
- Any existing caller that currently catches `TypeError` (unlikely but possible) would need to be updated to catch `RuntimeError` (or the new named exception) instead.
- If a retry mechanism is desired, it should be added in a separate pass; do not introduce retry logic as part of this minimal fix.
- Cosmos upsert on line 49 is only reached for successful payments — no change needed there.

## Unknowns
- None. Root cause is fully confirmed by static analysis and the minimal reproduction script.

## Escalation flag
`NONE`
