"""
bot/client.py
-------------
Binance Futures Testnet client wrapper.
Handles authentication, raw API calls, and exception normalisation.
"""

import os
import logging
from typing import Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

logger = logging.getLogger(__name__)


class BinanceTestnetClient:
    """
    Thin wrapper around python-binance for the USDT-M Futures Testnet.

    All order placement is routed through `place_order`, which:
      - forwards validated kwargs to the correct futures endpoint
      - catches Binance-specific exceptions and re-raises as RuntimeError
      - returns a normalised response dict
    """

    FUTURES_TESTNET_URL = "https://testnet.binancefuture.com"

    def __init__(self) -> None:
        api_key = os.getenv("API_KEY")
        api_secret = os.getenv("API_SECRET")

        if not api_key or not api_secret:
            raise EnvironmentError(
                "API_KEY and API_SECRET must be set in your .env file."
            )

        self._client = Client(
            api_key=api_key,
            api_secret=api_secret,
            testnet=True,
        )
        # Override the futures endpoint so all futures calls target the Binance testnet.
        self._client.FUTURES_URL = self.FUTURES_TESTNET_URL
        logger.info("BinanceTestnetClient initialised (testnet=True, testnet endpoint overridden).")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Place a futures order on the Binance Testnet.

        Parameters
        ----------
        symbol        : Trading pair, e.g. 'BTCUSDT'
        side          : 'BUY' or 'SELL'
        order_type    : 'LIMIT' or 'MARKET'
        quantity      : Order size in base asset units
        price         : Required for LIMIT orders; ignored for MARKET
        time_in_force : Default 'GTC' (Good Till Cancelled)

        Returns
        -------
        dict : Normalised order response with keys:
               orderId, symbol, status, avgPrice, origQty, side, type
        """
        kwargs = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        if order_type == "LIMIT":
            kwargs["price"] = str(price)
            kwargs["timeInForce"] = time_in_force

        try:
            raw = self._client.futures_create_order(**kwargs)
            logger.info("Order placed successfully: %s", raw)
            return self._normalise(raw)

        except BinanceAPIException as exc:
            logger.error(
                "BinanceAPIException [%s]: %s | params=%s",
                exc.status_code,
                exc.message,
                kwargs,
            )
            raise RuntimeError(
                f"Binance API error {exc.status_code}: {exc.message}"
            ) from exc

        except BinanceRequestException as exc:
            logger.error("BinanceRequestException: %s | params=%s", exc, kwargs)
            raise RuntimeError(f"Request failed: {exc}") from exc

    def get_account_balance(self) -> list[dict]:
        """Return futures wallet balances (non-zero assets only)."""
        try:
            balances = self._client.futures_account_balance()
            return [b for b in balances if float(b.get("balance", 0)) != 0]
        except BinanceAPIException as exc:
            logger.error("Failed to fetch balance: %s", exc)
            raise RuntimeError(f"Could not retrieve balance: {exc}") from exc
        except BinanceRequestException as exc:
            logger.error("Failed to fetch balance: %s", exc)
            raise RuntimeError(f"Could not retrieve balance: {exc}") from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(raw: dict) -> dict:
        """Extract the fields we care about from the raw Binance response."""
        return {
            "orderId": raw.get("orderId"),
            "symbol": raw.get("symbol"),
            "status": raw.get("status"),
            "avgPrice": raw.get("avgPrice", "0"),
            "origQty": raw.get("origQty"),
            "side": raw.get("side"),
            "type": raw.get("type"),
            "timeInForce": raw.get("timeInForce"),
            "updateTime": raw.get("updateTime"),
        }
