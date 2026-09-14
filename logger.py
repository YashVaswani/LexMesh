"""
LexMesh — Centralized Logging Configuration
============================================
All modules import the shared logger from here.

Log format  : [2026-09-14 18:23:01] [LEVEL   ] module_name : message
Log targets : Console (stdout) + lexmesh.log file (auto-rotated at 5 MB, 3 backups)
Log level   : INFO in production, DEBUG when LOG_LEVEL=DEBUG env var is set
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# ── Level ─────────────────────────────────────────────────────────────────────
_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()
_LEVEL = getattr(logging, _LEVEL_NAME, logging.INFO)

# ── Formatter ─────────────────────────────────────────────────────────────────
_FMT = "[%(asctime)s] [%(levelname)-8s] %(name)s : %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"
_formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

# ── Root logger ───────────────────────────────────────────────────────────────
_root = logging.getLogger("lexmesh")
_root.setLevel(_LEVEL)

# Avoid adding duplicate handlers if module is imported multiple times
if not _root.handlers:

    # Console handler
    _console = logging.StreamHandler()
    _console.setLevel(_LEVEL)
    _console.setFormatter(_formatter)
    _root.addHandler(_console)

    # Rotating file handler — writes to lexmesh.log next to this file
    _log_path = os.path.join(os.path.dirname(__file__), "lexmesh.log")
    try:
        _file_handler = RotatingFileHandler(
            _log_path,
            maxBytes=5 * 1024 * 1024,   # 5 MB per file
            backupCount=3,               # Keep last 3 rotated files
            encoding="utf-8",
        )
        _file_handler.setLevel(_LEVEL)
        _file_handler.setFormatter(_formatter)
        _root.addHandler(_file_handler)
    except Exception:
        # If file logging fails (e.g. read-only filesystem on Render), keep console only
        pass

# Silence noisy third-party libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("postgrest").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a child logger namespaced under 'lexmesh'.

    Usage:
        from logger import get_logger
        logger = get_logger(__name__)
        logger.info("Starting analysis...")
        logger.warning("API rate limited, retrying...")
        logger.error("Fatal error: %s", exc, exc_info=True)
    """
    return _root.getChild(name)
