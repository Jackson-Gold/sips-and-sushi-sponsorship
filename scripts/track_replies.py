"""Detect genuine replies to our outreach via IMAP and record them in status.json.

Matching strategy (most reliable first):
  1. The reply's `In-Reply-To` / `References` header contains a Message-ID we sent.
  2. Fallback: the sender's email address (or domain) matches a prospect we emailed.

Automated messages are NOT counted as replies:
  * Bounces / delivery-status notifications (mailer-daemon, multipart/report, etc.)
  * Out-of-office / vacation / auto-responder messages (Auto-Submitted, etc.)

Genuine replies are sentiment-analyzed (positive / neutral / negative) with a
lightweight offline lexicon so the dashboard can show interest levels.

Designed to run repeatedly (e.g. on a schedule in GitHub Actions); it is
idempotent and recomputes counts fresh each scan.
"""
from __future__ import annotations

import email
import imaplib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.utils import parseaddr

import config

MSGID_RE = re.compile(r"<[^>]+>")

# --- Automated-message detection ---
AUTO_FROM_LOCALPARTS = {
    "mailer-daemon", "postmaster", "no-reply", "noreply", "donotreply",
    "do-not-reply", "do_not_reply", "bounce", "bounces", "notifications",
    "notification", "auto-reply", "autoreply",
}
AUTO_SUBJECT_RE = re.compile(
    r"(out\s of\s office|out-of-office|automatic reply|auto[-\s]?reply|"
    r"auto[-\s]?response|away from (the )?office|on vacation|currently away|"
    r"delivery status notification|undeliverable|undelivered mail|"
    r"mail delivery (failed|subsystem)|returned mail|failure notice|"
    r"delivery has failed|address not found|message blocked)",
    re.IGNORECASE,
)

# --- Sentiment lexicon (phrase -> weight) ---
POSITIVE = {
    "interested": 2, "very interested": 3, "would love": 3, "we'd love": 3,
    "love to": 2, "happy to": 2, "glad to": 2, "excited": 3, "sounds great": 3,
    "sounds good": 2, "great idea": 2, "count us in": 3, "count me in": 3,
    "absolutely": 2, "definitely": 2, "let's": 1, "let us": 1, "schedule a call": 2,
    "set up a call": 2, "happy to help": 2, "yes": 1, "keen": 2, "delighted": 3,
    "wonderful": 2, "perfect": 2, "look forward": 2, "we can": 1, "we'd be happy": 3,
    "send more": 1, "tell me more": 2, "learn more": 1, "love this": 3,
    "in for": 2, "on board": 3, "would be great": 2,
}
NEGATIVE = {
    "not interested": 3, "no thank": 2, "no thanks": 2, "unfortunately": 2,
    "we decline": 3, "declining": 3, "have to decline": 3, "unable to": 2,
    "not able to": 2, "cannot": 1, "can't": 1, "won't be able": 2, "not a fit": 3,
    "not the right fit": 3, "no budget": 2, "not this year": 2, "pass on": 2,
    "we'll pass": 3, "regret": 2, "sorry": 1, "not participating": 3,
    "do not": 1, "unsubscribe": 3, "remove me": 3, "stop contacting": 3,
    "not at this time": 2, "not currently": 1, "no longer": 1,
}


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


def earliest_send_date(sends: dict):
    """Earliest send timestamp (minus a day of slack) as a datetime, or None."""
    stamps = []
    for rec in sends.values():
        ts = rec.get("timestamp")
        if ts:
            try:
                stamps.append(datetime.fromisoformat(ts))
            except ValueError:
                pass
    if not stamps:
        return None
    return min(stamps) - timedelta(days=1)


def is_automated(msg) -> bool:
    """True for bounces, delivery-status notifications, and auto-responders."""
    auto_sub = (msg.get("Auto-Submitted", "") or "").lower()
    if auto_sub and auto_sub != "no":
        return True
    if msg.get("X-Autoreply") or msg.get("X-Autorespond") or msg.get("X-Auto-Response-Suppress"):
        return True
    precedence = (msg.get("Precedence", "") or "").lower()
    if precedence in {"auto_reply", "bulk", "junk", "list"}:
        return True
    ctype = (msg.get("Content-Type", "") or "").lower()
    if ctype.startswith("multipart/report") or "delivery-status" in ctype:
        return True
    if msg.get("X-Failed-Recipients"):
        return True

    from_addr = parseaddr(msg.get("From", ""))[1].lower()
    local = from_addr.split("@")[0] if "@" in from_addr else from_addr
    if local in AUTO_FROM_LOCALPARTS:
        return True

    subject = decode(msg.get("Subject", ""))
    if AUTO_SUBJECT_RE.search(subject):
        return True
    return False


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


def get_body_text(msg) -> str:
    """Extract the human-written portion of a reply as plain text."""
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(
                part.get("Content-Disposition", "")
            ):
                text = _decode_payload(part)
                break
        if not text:
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    text = re.sub(r"<[^>]+>", " ", _decode_payload(part))
                    break
    else:
        text = _decode_payload(msg)
        if msg.get_content_type() == "text/html":
            text = re.sub(r"<[^>]+>", " ", text)

    # Trim quoted original message so we only score the new reply text.
    for marker in [r"\nOn .*wrote:", r"-----Original Message-----",
                   r"\nFrom:\s", r"________________________________"]:
        m = re.search(marker, text)
        if m:
            text = text[: m.start()]
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith(">")]
    return "\n".join(lines).strip()


def _decode_payload(part) -> str:
    try:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ""
        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    except Exception:  # noqa: BLE001
        return ""


def analyze_sentiment(text: str) -> tuple[str, int]:
    low = " " + re.sub(r"\s+", " ", text.lower()) + " "
    score = 0
    for phrase, weight in POSITIVE.items():
        score += weight * low.count(phrase)
    for phrase, weight in NEGATIVE.items():
        score -= weight * low.count(phrase)
    if score > 1:
        return "positive", score
    if score < 0:
        return "negative", score
    return "neutral", score


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

    # Only scan mail since (a day before) the first outreach send - much faster
    # than scanning an entire personal inbox.
    since_dt = earliest_send_date(sends)
    if since_dt:
        criteria = ["SINCE", since_dt.strftime("%d-%b-%Y")]
    else:
        criteria = ["ALL"]
    typ, data = imap.search(None, *criteria)
    if typ != "OK":
        imap.logout()
        sys.exit("IMAP search failed.")

    ids = data[0].split()
    matches: dict[str, dict] = {}
    filtered_auto = 0

    header_fields = ("FROM SUBJECT DATE IN-REPLY-TO REFERENCES AUTO-SUBMITTED "
                     "X-AUTOREPLY X-AUTORESPOND X-AUTO-RESPONSE-SUPPRESS PRECEDENCE "
                     "CONTENT-TYPE X-FAILED-RECIPIENTS")

    for num in ids:
        typ, hdr_data = imap.fetch(num, f"(BODY.PEEK[HEADER.FIELDS ({header_fields})])")
        if typ != "OK" or not hdr_data or not hdr_data[0]:
            continue
        hdr = email.message_from_bytes(hdr_data[0][1])

        if is_automated(hdr):
            # Only count it as filtered if it would otherwise have matched us.
            if match_prospect(hdr, by_msgid, by_email, by_domain):
                filtered_auto += 1
            continue

        pid = match_prospect(hdr, by_msgid, by_email, by_domain)
        if not pid:
            continue

        # Genuine reply: fetch the full body for sentiment.
        typ, full = imap.fetch(num, "(BODY.PEEK[])")
        body = ""
        if typ == "OK" and full and full[0]:
            body = get_body_text(email.message_from_bytes(full[0][1]))

        acc = matches.setdefault(pid, {
            "count": 0, "last_from": "", "last_subject": "", "text": "",
        })
        acc["count"] += 1
        acc["last_from"] = parseaddr(hdr.get("From", ""))[1]
        acc["last_subject"] = decode(hdr.get("Subject", ""))
        acc["text"] += "\n" + body

    imap.logout()

    for pid, acc in matches.items():
        prev = status.get(pid, {})
        sentiment, score = analyze_sentiment(acc["text"])
        status[pid] = {
            "id": pid,
            "company": sends.get(pid, {}).get("company", ""),
            "status": "replied",
            "reply_count": acc["count"],
            "sentiment": sentiment,
            "sentiment_score": score,
            "first_reply_at": prev.get("first_reply_at", now_iso()),
            "last_reply_at": now_iso(),
            "last_from": acc["last_from"],
            "last_subject": acc["last_subject"],
        }

    # Drop companies that no longer have a genuine reply (e.g. only bounces remain).
    for pid in list(status.keys()):
        if pid not in matches:
            del status[pid]

    save_json(config.STATUS_JSON, status)
    print(f"Scanned {len(ids)} messages. Genuine replies: {len(status)} companies. "
          f"Filtered auto/bounce: {filtered_auto}. -> {config.STATUS_JSON}")


if __name__ == "__main__":
    main()
