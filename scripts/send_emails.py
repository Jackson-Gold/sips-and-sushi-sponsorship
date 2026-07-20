"""Render and send personalized sponsorship emails.

Reads `data/prospects.json`, renders each company's hyper-tailored subject/body
from `email_content.py` (with the event logo embedded), and either:
  * `--dry-run` (default off): writes preview `.eml` files to `previews/` without
    sending, or
  * live: sends via SMTP with a throttle between messages.

Every attempt is recorded in `data/sends.json` keyed by prospect id, including a
unique Message-ID used later for reply matching. Route-only prospects (no email)
are logged as `skipped`.
"""
from __future__ import annotations

import argparse
import json
import smtplib
import sys
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

import config
import email_content


def load_json(path, default):
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def load_logo() -> bytes | None:
    logo_path = config.ROOT / "assets" / "sips_and_sushi_logo.png"
    return logo_path.read_bytes() if logo_path.exists() else None


def connect_smtp() -> smtplib.SMTP:
    smtp = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=60)
    smtp.ehlo()
    smtp.starttls()
    smtp.login(config.SMTP_USER, config.SMTP_PASS)
    return smtp


def ensure_alive(smtp: smtplib.SMTP) -> smtplib.SMTP:
    """Return a live SMTP connection, reconnecting if the current one dropped."""
    try:
        if smtp is not None and smtp.noop()[0] == 250:
            return smtp
    except Exception:  # noqa: BLE001
        pass
    try:
        if smtp is not None:
            smtp.close()
    except Exception:  # noqa: BLE001
        pass
    return connect_smtp()


def send_with_retry(smtp: smtplib.SMTP, msg) -> smtplib.SMTP:
    """Send a message, reconnecting once on a dropped connection."""
    smtp = ensure_alive(smtp)
    try:
        smtp.send_message(msg)
        return smtp
    except smtplib.SMTPServerDisconnected:
        smtp = connect_smtp()
        smtp.send_message(msg)
        return smtp


def make_email(prospect: dict, message_id: str, logo_bytes: bytes | None) -> tuple[EmailMessage, str]:
    """Build the tailored email for a prospect. Returns (message, subject)."""
    subject = email_content.build_subject(prospect)
    msg = EmailMessage()
    msg["From"] = formataddr((config.FROM_NAME, config.FROM_EMAIL))
    msg["To"] = prospect["email"]
    msg["Reply-To"] = config.REPLY_TO
    msg["Subject"] = subject
    msg["Message-ID"] = message_id
    msg["List-Unsubscribe"] = f"<mailto:{config.ORGANIZER['opt_out_email']}?subject=unsubscribe>"

    msg.set_content(email_content.to_text(prospect))
    logo_cid = None
    if logo_bytes:
        logo_cid = make_msgid(domain=config.FROM_EMAIL.split("@")[-1])[1:-1]
    msg.add_alternative(email_content.to_html(prospect, logo_cid), subtype="html")
    if logo_bytes:
        msg.get_payload()[-1].add_related(
            logo_bytes, maintype="image", subtype="png", cid=f"<{logo_cid}>",
            filename="sips_and_sushi_logo.png",
        )
    return msg, subject


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(description="Send personalized sponsorship emails.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Write .eml previews instead of sending.")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max number of emails to send this run (0 = no limit).")
    parser.add_argument("--resend", action="store_true",
                        help="Re-send even if already marked sent.")
    parser.add_argument("--only", type=str, default="",
                        help="Comma-separated prospect ids to restrict the run to.")
    parser.add_argument("--test-to", type=str, default="",
                        help="Deliver every message to this address instead of the "
                             "company (for testing). Nothing is logged to sends.json.")
    args = parser.parse_args()

    prospects = load_json(config.PROSPECTS_JSON, None)
    if prospects is None:
        sys.exit("Missing data/prospects.json. Run build_data.py first.")

    sends = load_json(config.SENDS_JSON, {})
    logo_bytes = load_logo()
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    test_to = args.test_to.strip()
    if test_to:
        args.dry_run = False  # a test send must actually go out (to yourself)

    live = not args.dry_run
    if live and (not config.SMTP_USER or not config.SMTP_PASS):
        sys.exit("SMTP_USER / SMTP_PASS not set. Use --dry-run or configure .env.")

    if args.dry_run:
        config.PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    smtp = None
    if live:
        smtp = connect_smtp()

    sent_count = 0
    try:
        for prospect in prospects:
            pid = prospect["id"]
            if only and pid not in only:
                continue

            existing = sends.get(pid)
            if existing and existing.get("status") == "sent" and not args.resend and not test_to:
                continue

            if prospect["status_class"] == "route_only" and not test_to:
                sends[pid] = {
                    "id": pid,
                    "company": prospect["company"],
                    "to": "",
                    "status": "skipped",
                    "reason": "no_email",
                    "contact_route": prospect.get("contact_route", ""),
                    "phone": prospect.get("phone", ""),
                    "source_url": prospect.get("source_url", ""),
                    "message_id": "",
                    "subject": "",
                    "timestamp": now_iso(),
                }
                continue

            message_id = make_msgid(domain=config.FROM_EMAIL.split("@")[-1])
            msg, subject = make_email(prospect, message_id, logo_bytes)

            if test_to:
                del msg["To"]
                msg["To"] = test_to
                try:
                    smtp = send_with_retry(smtp, msg)
                    print(f"[test] {pid} rendered -> delivered to {test_to} (not logged)")
                    sent_count += 1
                    time.sleep(config.SEND_THROTTLE_SECONDS)
                except Exception as exc:  # noqa: BLE001
                    print(f"[failed] {pid}: {exc}")
                if args.limit and sent_count >= args.limit:
                    print(f"Reached limit of {args.limit}.")
                    break
                continue

            if args.dry_run:
                out = config.PREVIEWS_DIR / f"{pid}.eml"
                with open(out, "wb") as fh:
                    fh.write(bytes(msg))
                sends.setdefault(pid, {
                    "id": pid,
                    "company": prospect["company"],
                    "to": prospect["email"],
                    "status": "preview",
                    "reason": "dry_run",
                    "message_id": message_id,
                    "subject": subject,
                    "timestamp": now_iso(),
                })
                print(f"[preview] {pid} -> {out.name}")
                sent_count += 1
            else:
                try:
                    smtp = send_with_retry(smtp, msg)
                    sends[pid] = {
                        "id": pid,
                        "company": prospect["company"],
                        "to": prospect["email"],
                        "status": "sent",
                        "reason": "",
                        "message_id": message_id,
                        "subject": subject,
                        "timestamp": now_iso(),
                    }
                    print(f"[sent] {pid} -> {prospect['email']}")
                    sent_count += 1
                    time.sleep(config.SEND_THROTTLE_SECONDS)
                except Exception as exc:  # noqa: BLE001
                    sends[pid] = {
                        "id": pid,
                        "company": prospect["company"],
                        "to": prospect["email"],
                        "status": "failed",
                        "reason": str(exc),
                        "message_id": message_id,
                        "subject": subject,
                        "timestamp": now_iso(),
                    }
                    print(f"[failed] {pid}: {exc}")

            if args.limit and sent_count >= args.limit:
                print(f"Reached limit of {args.limit}.")
                break
    finally:
        if smtp is not None:
            try:
                smtp.quit()
            except Exception:  # noqa: BLE001
                pass
        save_json(config.SENDS_JSON, sends)

    mode = "previews written" if args.dry_run else "emails sent"
    print(f"Done. {sent_count} {mode}. Log: {config.SENDS_JSON}")


if __name__ == "__main__":
    main()
