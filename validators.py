"""
bot/validators.py
-----------------
Input validation layer.
All checks run BEFORE any network call is made, keeping API error noise low.
"""

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Validated order dataclass — the single object passed downstream
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ValidatedOrder:
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class ValidationError(ValueError):
    """Raised when user-supplied order parameters fail validation."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"LIMIT", "MARKET"}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def validate_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> ValidatedOrder:
    """
    Validate all order parameters and return a `ValidatedOrder`.

    Raises
    ------
    ValidationError : with a descriptive message on the first failing check.
    """
    _validate_symbol(symbol)
    _validate_side(side)
    _validate_order_type(order_type)
    _validate_quantity(quantity)
    price = _validate_price(order_type, price)

    return ValidatedOrder(
        symbol=symbol.upper().strip(),
        side=side.upper().strip(),
        order_type=order_type.upper().strip(),
        quantity=float(quantity),
        price=price,
    )


# ---------------------------------------------------------------------------
# Private validators
# ---------------------------------------------------------------------------

def _validate_symbol(symbol: str) -> None:
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValidationError("Symbol must be a non-empty string (e.g. BTCUSDT).")
    cleaned = symbol.upper().strip()
    if not cleaned.isalpha():
        raise ValidationError(
            f"Symbol '{symbol}' contains invalid characters. "
            "Expected uppercase letters only (e.g. BTCUSDT)."
        )


def _validate_side(side: str) -> None:
    if not isinstance(side, str) or side.upper().strip() not in VALID_SIDES:
        raise ValidationError(
            f"Side must be one of {sorted(VALID_SIDES)}. Got: '{side}'."
        )


def _validate_order_type(order_type: str) -> None:
    if not isinstance(order_type, str) or order_type.upper().strip() not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Order type must be one of {sorted(VALID_ORDER_TYPES)}. Got: '{order_type}'."
        )


def _validate_quantity(quantity: float) -> None:
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Quantity must be a positive number. Got: '{quantity}'."
        )
    if qty <= 0:
        raise ValidationError(
            f"Quantity must be greater than 0. Got: {qty}."
        )


def _validate_price(order_type: str, price: Optional[float]) -> Optional[float]:
    """
    LIMIT  → price is required and must be a positive float.
    MARKET → price is ignored (returns None with a soft warning).
    """
    ot = order_type.upper().strip()

    if ot == "LIMIT":
        if price is None:
            raise ValidationError(
                "A 'price' is required for LIMIT orders."
            )
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValidationError(
                f"Price must be a positive number. Got: '{price}'."
            )
        if p <= 0:
            raise ValidationError(
                f"Price must be greater than 0. Got: {p}."
            )
        return p

    # MARKET order — price is irrelevant
    if price is not None:
        import warnings
        warnings.warn(
            "Price parameter is ignored for MARKET orders.",
            UserWarning,
            stacklevel=3,
        )
    return None
