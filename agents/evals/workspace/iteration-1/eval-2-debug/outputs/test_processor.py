"""Failing pytest test reproducing the None-unpack bug in process_order.

Bug: process_order calls _call_payment_gateway and unconditionally unpacks
the result on line 46. When the gateway times out, the function returns None,
causing:
    TypeError: cannot unpack non-iterable NoneType object
"""
from __future__ import annotations

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Make src/orders importable when running from the repo root or the fixture dir
FIXTURE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(FIXTURE_DIR, ".."))

from processor import process_order, _call_payment_gateway  # noqa: E402


VALID_CART = {"id": "cart-1", "token": "tok_test", "total": 99.99}


class TestCallPaymentGatewayReturnsNoneOnTimeout:
    """_call_payment_gateway must return None when the gateway times out."""

    def test_returns_none_on_timeout(self):
        """Confirms _call_payment_gateway returns None (not raises) on timeout."""
        import httpx

        with patch("httpx.post", side_effect=httpx.TimeoutException("timed out")):
            result = _call_payment_gateway(VALID_CART)

        assert result is None, (
            "_call_payment_gateway should return None on TimeoutException"
        )


class TestProcessOrderHandlesPaymentGatewayNone:
    """process_order must NOT crash with TypeError when payment gateway returns None."""

    def test_raises_informative_error_instead_of_type_error(self):
        """
        FAILING TEST — demonstrates the bug.

        When _call_payment_gateway returns None, process_order should raise a
        meaningful exception (e.g. RuntimeError / PaymentGatewayError) rather
        than an unhandled TypeError from the tuple-unpack on line 46.

        Expected: RuntimeError (or a named payment error) is raised
        Actual:   TypeError: cannot unpack non-iterable NoneType object
        """
        with patch("processor._call_payment_gateway", return_value=None), \
             patch("processor.CosmosClient"), \
             patch("processor.DefaultAzureCredential"):
            # The bug makes this raise TypeError, NOT the informative error below.
            # After the fix this assertion must pass.
            with pytest.raises((RuntimeError, ValueError), match=r"[Pp]ayment"):
                process_order(VALID_CART)

    def test_no_type_error_on_gateway_timeout(self):
        """
        FAILING TEST — end-to-end reproduction of the reported crash.

        Simulates a real timeout from httpx so no mocking of _call_payment_gateway
        is needed. The unpack on line 46 must not reach execution.
        """
        import httpx

        with patch("httpx.post", side_effect=httpx.TimeoutException("gateway slow")):
            # Patch CosmosClient so we don't need real Azure credentials
            with patch("processor.CosmosClient"):
                with pytest.raises(TypeError):
                    # THIS should NOT raise TypeError after the fix.
                    # We explicitly assert TypeError here to prove the bug is present.
                    process_order(VALID_CART)

        # After fix: the block above should raise RuntimeError/ValueError, not TypeError.
        # Flip this test to use pytest.raises((RuntimeError, ValueError)) post-fix.
