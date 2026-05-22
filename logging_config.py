"""
bot/logging_config.py
---------------------
Configures the root logger to write to both:
  - stdout (console) — colourised for readability
  - trading_bot.log  — JSON-friendly plain text for audit/delivery
"""

import logging
import sys
from pathlib import Path

LOG_FILE = Path("trading_bot.log")

# ---------------------------------------------------------------------------
# ANSI colour helpers (console only)
# ---------------------------------------------------------------------------

RESET = "\033[0m"
COLOURS = {
    logging.DEBUG:    "\033[36m",   # cyan
    logging.INFO:     "\033[32m",   # green
    logging.WARNING:  "\033[33m",   # yellow
    logging.ERROR:    "\033[31m",   # red
    logging.CRITICAL: "\033[35m",   # magenta
}


class ColouredFormatter(logging.Formatter):
    """Apply ANSI colour codes to the level name for console output."""

    def format(self, record: logging.LogRecord) -> str:
        colour = COLOURS.get(record.levelno, RESET)
        record.levelname = f"{colour}{record.levelname:<8}{RESET}"
        return super().format(record)


# ---------------------------------------------------------------------------
# Public setup function
# ---------------------------------------------------------------------------

def setup_logging(level: int = logging.INFO) -> None:
    """
    Call once at application startup (e.g. top of cli.py).

    Handlers
    --------
    console  : ColouredFormatter → stdout, level=INFO
    file     : Plain formatter   → trading_bot.log, level=DEBUG (captures all)
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # let handlers filter independently

    # Avoid duplicate handlers if called more than once (e.g. in tests)
    if root.handlers:
        return

    # --- Console handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(
        ColouredFormatter(
            fmt="%(asctime)s  %(levelname)s  %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # --- File handler ---
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    root.addHandler(console_handler)
    root.addHandler(file_handler)
