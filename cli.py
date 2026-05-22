#!/usr/bin/env python3
"""
cli.py
------
Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples
--------------
# LIMIT buy
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.5 --price 60000

# MARKET sell
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 1.2

# Check wallet balance
python cli.py --balance
"""

import argparse
import json
import sys

from dotenv import load_dotenv

from bot.logging_config import setup_logging
from bot.validators import validate_order, ValidationError
from bot.client import BinanceTestnetClient

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()          # reads API_KEY / API_SECRET from .env
setup_logging()        # console + file handlers

import logging
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Binance USDT-M Futures Testnet — CLI Order Placer",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python cli.py --symbol BTCUSDT --side BUY --type LIMIT "
            "--quantity 0.5 --price 60000\n"
            "  python cli.py --symbol ETHUSDT --side SELL --type MARKET "
            "--quantity 1.2\n"
            "  python cli.py --balance"
        ),
    )

    order_group = parser.add_argument_group("Order parameters")
    order_group.add_argument(
        "--symbol", type=str, metavar="SYMBOL",
        help="Trading pair (e.g. BTCUSDT)",
    )
    order_group.add_argument(
        "--side", type=str, choices=["BUY", "SELL"],
        metavar="SIDE", help="BUY or SELL",
    )
    order_group.add_argument(
        "--type", dest="order_type", type=str,
        choices=["LIMIT", "MARKET"], metavar="TYPE",
        help="Order type: LIMIT or MARKET",
    )
    order_group.add_argument(
        "--quantity", type=float, metavar="QTY",
        help="Order size in base asset units",
    )
    order_group.add_argument(
        "--price", type=float, metavar="PRICE", default=None,
        help="Limit price (required for LIMIT orders)",
    )

    parser.add_argument(
        "--balance", action="store_true",
        help="Display futures wallet balances and exit",
    )

    return parser


# ---------------------------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------------------------

DIVIDER = "─" * 52

def _print_order_summary(order: dict) -> None:
    avg = float(order.get("avgPrice") or 0)
    avg_display = f"${avg:,.2f}" if avg else "pending (LIMIT on book)"

    print(f"\n{'━' * 52}")
    print(f"  ✅  ORDER PLACED SUCCESSFULLY")
    print(DIVIDER)
    print(f"  Order ID   : {order['orderId']}")
    print(f"  Symbol     : {order['symbol']}")
    print(f"  Side       : {order['side']}")
    print(f"  Type       : {order['type']}")
    print(f"  Quantity   : {order['origQty']}")
    print(f"  Avg Price  : {avg_display}")
    print(f"  Status     : {order['status']}")
    if order.get("timeInForce"):
        print(f"  TIF        : {order['timeInForce']}")
    print(f"{'━' * 52}\n")


def _print_balances(balances: list[dict]) -> None:
    if not balances:
        print("  No non-zero balances found.")
        return
    print(f"\n{'━' * 52}")
    print("  FUTURES WALLET BALANCES (Testnet)")
    print(DIVIDER)
    for b in balances:
        print(f"  {b['asset']:<10} {float(b['balance']):>15,.4f}")
    print(f"{'━' * 52}\n")


def _print_failure(message: str) -> None:
    print(f"\n{'━' * 52}")
    print(f"  ❌  ORDER FAILED")
    print(DIVIDER)
    print(f"  Reason : {message}")
    print(f"{'━' * 52}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # ── Balance check shortcut ─────────────────────────────────────────────
    if args.balance:
        try:
            client = BinanceTestnetClient()
            balances = client.get_account_balance()
            _print_balances(balances)
            return 0
        except Exception as exc:
            _print_failure(str(exc))
            return 1

    # ── Require order parameters when not using --balance ──────────────────
    required = ("symbol", "side", "order_type", "quantity")
    missing = [f"--{f.replace('_', '-')}" for f in required if not getattr(args, f)]
    if missing:
        parser.error(f"The following arguments are required: {', '.join(missing)}")

    logger.info(
        "Received order request: symbol=%s side=%s type=%s qty=%s price=%s",
        args.symbol, args.side, args.order_type, args.quantity, args.price,
    )

    # ── Validate ───────────────────────────────────────────────────────────
    try:
        validated = validate_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        _print_failure(f"Validation error — {exc}")
        return 1

    logger.info("Validation passed: %s", validated)

    # ── Place order ────────────────────────────────────────────────────────
    try:
        client = BinanceTestnetClient()
        order = client.place_order(
            symbol=validated.symbol,
            side=validated.side,
            order_type=validated.order_type,
            quantity=validated.quantity,
            price=validated.price,
        )
    except RuntimeError as exc:
        logger.error("Order placement failed: %s", exc)
        _print_failure(str(exc))
        return 1

    # ── Print summary ──────────────────────────────────────────────────────
    _print_order_summary(order)
    logger.info("Order summary: %s", json.dumps(order, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
