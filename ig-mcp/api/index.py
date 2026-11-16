"""Vercel Python runtime entry point; Vercel serves the ASGI ``app`` exported here."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.http_app import app  # noqa: E402,F401
