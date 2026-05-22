"""
tests/test_validators.py
------------------------
Unit tests for the validation layer.
No API keys or network access required.
"""

import pytest
from bot.validators import validate_order, ValidationError, ValidatedOrder


# ── Happy paths ────────────────────────────────────────────────────────────

def test_valid_limit_order():
    order = validate_order("btcusdt", "buy", "limit", 0.5, 60000)
    assert isinstance(order, ValidatedOrder)
    assert order.symbol == "BTCUSDT"
    assert order.side == "BUY"
    assert order.order_type == "LIMIT"
    assert order.quantity == 0.5
    assert order.price == 60000.0


def test_valid_market_order_no_price():
    order = validate_order("ETHUSDT", "SELL", "MARKET", 1.2)
    assert order.price is None
    assert order.order_type == "MARKET"


def test_market_order_price_ignored(recwarn):
    order = validate_order("ETHUSDT", "SELL", "MARKET", 1.2, price=9999)
    assert order.price is None
    assert len(recwarn) == 1
    assert "ignored" in str(recwarn[0].message).lower()


# ── Symbol validation ──────────────────────────────────────────────────────

def test_symbol_normalised_to_uppercase():
    order = validate_order("btcusdt", "BUY", "MARKET", 1.0)
    assert order.symbol == "BTCUSDT"


def test_symbol_empty_raises():
    with pytest.raises(ValidationError, match="non-empty"):
        validate_order("", "BUY", "MARKET", 1.0)


def test_symbol_with_digits_raises():
    with pytest.raises(ValidationError, match="invalid characters"):
        validate_order("BTC123", "BUY", "MARKET", 1.0)


# ── Side validation ────────────────────────────────────────────────────────

def test_invalid_side_raises():
    with pytest.raises(ValidationError, match="BUY.*SELL|SELL.*BUY"):
        validate_order("BTCUSDT", "LONG", "MARKET", 1.0)


# ── Order type validation ──────────────────────────────────────────────────

def test_invalid_order_type_raises():
    with pytest.raises(ValidationError, match="LIMIT.*MARKET|MARKET.*LIMIT"):
        validate_order("BTCUSDT", "BUY", "STOP", 1.0)


# ── Quantity validation ────────────────────────────────────────────────────

def test_zero_quantity_raises():
    with pytest.raises(ValidationError, match="greater than 0"):
        validate_order("BTCUSDT", "BUY", "MARKET", 0)


def test_negative_quantity_raises():
    with pytest.raises(ValidationError, match="greater than 0"):
        validate_order("BTCUSDT", "BUY", "MARKET", -1)


def test_string_quantity_raises():
    with pytest.raises(ValidationError, match="positive number"):
        validate_order("BTCUSDT", "BUY", "MARKET", "abc")


# ── Price validation ───────────────────────────────────────────────────────

def test_limit_without_price_raises():
    with pytest.raises(ValidationError, match="price.*required|required.*price"):
        validate_order("BTCUSDT", "BUY", "LIMIT", 0.5)


def test_limit_with_zero_price_raises():
    with pytest.raises(ValidationError, match="greater than 0"):
        validate_order("BTCUSDT", "BUY", "LIMIT", 0.5, price=0)


def test_limit_with_negative_price_raises():
    with pytest.raises(ValidationError, match="greater than 0"):
        validate_order("BTCUSDT", "BUY", "LIMIT", 0.5, price=-100)
