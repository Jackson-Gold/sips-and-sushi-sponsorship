"""Central configuration and path helpers.

Values are read from environment variables (optionally loaded from a local
`.env` file). Event/organizer defaults are provided so the pipeline and email
previews work out of the box; override them via `.env` or GitHub Actions
secrets before sending for real.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv is optional at runtime
    pass


# --- Paths ---
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DOCS_DATA_DIR = ROOT / "docs" / "data"
TEMPLATES_DIR = ROOT / "templates"
PREVIEWS_DIR = ROOT / "previews"

XLSX_PATH = DATA_DIR / "cocktail_event_sponsorship_contacts_100_companies.xlsx"
PROSPECTS_JSON = DATA_DIR / "prospects.json"
SENDS_JSON = DATA_DIR / "sends.json"
STATUS_JSON = DATA_DIR / "status.json"
STATS_JSON = DOCS_DATA_DIR / "stats.json"


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


# --- SMTP (outgoing) ---
SMTP_HOST = _env("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(_env("SMTP_PORT", "587") or "587")
SMTP_USER = _env("SMTP_USER")
SMTP_PASS = _env("SMTP_PASS")
FROM_EMAIL = _env("FROM_EMAIL") or SMTP_USER
FROM_NAME = _env("FROM_NAME", "Event Partnerships")
REPLY_TO = _env("REPLY_TO") or FROM_EMAIL

# --- IMAP (reply tracking) ---
IMAP_HOST = _env("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(_env("IMAP_PORT", "993") or "993")
IMAP_USER = _env("IMAP_USER") or SMTP_USER
IMAP_PASS = _env("IMAP_PASS") or SMTP_PASS
IMAP_FOLDER = _env("IMAP_FOLDER", "INBOX")

# --- Sending controls ---
SEND_THROTTLE_SECONDS = float(_env("SEND_THROTTLE_SECONDS", "8") or "8")

# --- Event / organizer context (available to templates) ---
EVENT = {
    "name": _env("EVENT_NAME", "The Manhattan Mix: A Craft Cocktail Evening"),
    "date": _env("EVENT_DATE", "October 24, 2026"),
    "city": _env("EVENT_CITY", "New York, NY"),
    "venue": _env("EVENT_VENUE", "The Foundry, Long Island City"),
    "attendance": _env("EVENT_ATTENDANCE", "250"),
    "audience": _env(
        "EVENT_AUDIENCE",
        "hospitality professionals, food & beverage press, and cocktail enthusiasts",
    ),
    "website": _env("EVENT_WEBSITE", "https://example.com/cocktail-event"),
}

ORGANIZER = {
    "name": _env("ORGANIZER_NAME", "Your Name"),
    "title": _env("ORGANIZER_TITLE", "Event Director"),
    "org": _env("ORGANIZER_ORG", "Your Organization"),
    "phone": _env("ORGANIZER_PHONE", "+1 (555) 123-4567"),
    "address": _env("PHYSICAL_ADDRESS", "123 Example Street, Suite 100, New York, NY 10001"),
    "opt_out_email": _env("OPT_OUT_EMAIL", "unsubscribe@example.com"),
}
