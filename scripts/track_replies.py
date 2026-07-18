"""Detect replies to our outreach via IMAP and record them in `data/status.json`.

Matching strategy (most reliable first):
  1. The reply's `In-Reply-To` / `References` header contains a Message-ID we sent.
  2. Fallback: the sender's email address (or domain) matches a prospect we emailed.

Designed to run repeatedly (e.g. on a schedule in GitHub Actions); it is
idempotent and only records the first reply time plus a running reply count.
"""
from __future__ import annotations

import email
import imaplib
import json
import re
import sys
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.utils import parseaddr

import config

MSGID_RE = re.compile(r"<[^>]+>")


def load_json(path, default):
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def decode(value: str) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:  # noqa: BLE001
        return value


def build_lookups(sends: dict):
    by_msgid: dict[str, str] = {}
    by_email: dict[str, str] = {}
    by_domain: dict[str, str] = {}
    for pid, rec in sends.items():
        if rec.get("status") not in {"sent", "failed"}:
            continue
        mid = rec.get("message_id", "")
        if mid:
            by_msgid[mid.strip().lower()] = pid
        to = (rec.get("to") or "").lower()
        if to:
            by_email[to] = pid
            by_domain.setdefault(to.split("@")[-1], pid)
    return by_msgid, by_email, by_domain


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def match_prospect(msg, by_msgid, by_email, by_domain) -> str | None:
    refs = " ".join(filter(None, [msg.get("In-Reply-To", ""), msg.get("References", "")]))
    for mid in MSGID_RE.findall(refs):
        pid = by_msgid.get(mid.strip().lower())
        if pid:
            return pid

    from_addr = parseaddr(msg.get("From", ""))[1].lower()
    if from_addr in by_email:
        return by_email[from_addr]
    if from_addr and "@" in from_addr:
        return by_domain.get(from_addr.split("@")[-1])
    return None


def main() -> None:
    sends = load_json(config.SENDS_JSON, {})
    if not sends:
        print("No sends recorded yet; nothing to match. Writing empty status.")
        save_json(config.STATUS_JSON, load_json(config.STATUS_JSON, {}))
        return

    if not config.IMAP_USER or not config.IMAP_PASS:
        sys.exit("IMAP_USER / IMAP_PASS not set. Configure .env or Actions secrets.")

    by_msgid, by_email, by_domain = build_lookups(sends)
    status = load_json(config.STATUS_JSON, {})

    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    imap.login(config.IMAP_USER, config.IMAP_PASS)
    imap.select(config.IMAP_FOLDER, readonly=True)

    typ, data = imap.search(None, "ALL")
    if typ != "OK":
        imap.logout()
        sys.exit("IMAP search failed.")

    ids = data[0].split()
    # Recompute matches fresh each scan so counts stay accurate on repeat runs.
    matches: dict[str, dict] = {}
    for num in ids:
        typ, msg_data = imap.fetch(
            num, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE IN-REPLY-TO REFERENCES)])"
        )
        if typ != "OK" or not msg_data or not msg_data[0]:
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        pid = match_prospect(msg, by_msgid, by_email, by_domain)
        if not pid:
            continue

        acc = matches.setdefault(pid, {"count": 0, "last_from": "", "last_subject": ""})
        acc["count"] += 1
        acc["last_from"] = parseaddr(msg.get("From", ""))[1]
        acc["last_subject"] = decode(msg.get("Subject", ""))

    imap.logout()

    for pid, acc in matches.items():
        prev = status.get(pid, {})
        status[pid] = {
            "id": pid,
            "company": sends.get(pid, {}).get("company", ""),
            "status": "replied",
            "reply_count": acc["count"],
            "first_reply_at": prev.get("first_reply_at", now_iso()),
            "last_reply_at": now_iso(),
            "last_from": acc["last_from"],
            "last_subject": acc["last_subject"],
        }

    save_json(config.STATUS_JSON, status)
    print(f"Scanned {len(ids)} messages. Companies with replies: {len(status)}. "
          f"-> {config.STATUS_JSON}")


if __name__ == "__main__":
    main()
