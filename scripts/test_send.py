"""Send 5 hyper-tailored sample sponsorship emails to yourself for review.

Unlike the production `send_emails.py` (which renders a single template for all
companies), this test contains 5 hand-written, company-specific emails built
around each brand's real products and a concrete cocktail idea. Every message is
delivered to YOU (not the companies) so you can proofread tone and tailoring.

Usage:
    python scripts/test_send.py               # sends all 5 to FROM_EMAIL
    python scripts/test_send.py --to me@x.com # override recipient
"""
from __future__ import annotations

import argparse
import re
import smtplib
import sys
import time
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

import config

SIGNATURE = """Cheers,

Jackson Gold
jacksongold04@gmail.com"""


# Each entry is one hand-tailored email. `real_to` is who it WOULD go to in a
# real send; during this test everything is delivered to --to instead.
EMAILS = [
    {
        "id": "east-imperial",
        "company": "East Imperial",
        "real_to": "info@eastimperial.com",
        "subject": "East Imperial x our NYC cocktail showcase",
        "body": """Hi East Imperial team,

I hope you're doing well!

My name is Jackson Gold, and I'm one of the organizers of **Sips and Sushi**, a cocktail showcase we're hosting in New York featuring a group of incredibly talented up-and-coming bartenders - paired, as the name suggests, with fresh, chef-prepared sushi all evening.

This year will be the **fifth edition** of the showcase, and it's become one of our favorite events to put together. We'll have more than 100 guests spending the evening tasting original cocktails, pairing them with the sushi, meeting the bartenders behind the drinks, and discovering the products that make them special.

I've been a fan of **East Imperial** for a while now - your mixers are the kind of thing bartenders genuinely geek out over - and I'd love to include them in this year's event. I can already picture one of the bartenders building a crisp, Tokyo-style highball around **East Imperial Yuzu Tonic**, letting that bright citrus and dry bitterness carry a great gin. A well-made G&T with the right tonic is one of the most underrated pours at any party - and a bright, citrus-forward highball is honestly a perfect match for a night of fresh sushi.

The audience is made up of **bartenders, cocktail enthusiasts, and hospitality professionals**, so it's a group that genuinely appreciates discovering well-made products rather than simply trying another drink - and they absolutely notice the difference a serious tonic makes.

We're already lining up a handful of well-known spirits brands for this year's showcase, and we'd love to have **East Imperial** alongside them.

Just to be clear, taking part is completely free - there's no sponsorship fee of any kind, only whatever product or support you're comfortable providing. If you'd be interested, we'd be glad to feature whatever makes the most sense from your perspective - whether that's a few cases of tonics and ginger beer for the bartenders to build highballs with, branded glassware, bar tools, or anything else you'd like guests to experience. If there's a particular tonic you'd love us to feature, we'd be excited to build a signature serve around it.

If you'd like, I'd be happy to send over a little more about the event, the bartenders, and what we have planned.

Thanks so much for taking the time to read this. We'd love the opportunity to introduce **East Imperial** to our guests and hopefully create a few new fans along the way.""",
    },
    {
        "id": "aplos",
        "company": "Aplós",
        "real_to": "hello@aplos.world",
        "subject": "Aplós x our NYC cocktail showcase (a zero-proof centerpiece)",
        "body": """Hi Aplós team,

I hope you're doing well!

My name is Jackson Gold, and I'm one of the organizers of **Sips and Sushi**, a cocktail showcase we're hosting in New York featuring a group of incredibly talented up-and-coming bartenders - paired, as the name suggests, with fresh, chef-prepared sushi all evening.

This year will be the **fifth edition** of the showcase, and it's become one of our favorite events to put together. We'll have more than 100 guests spending the evening tasting original cocktails, pairing them with the sushi, meeting the bartenders behind the drinks, and discovering the products that make them special.

I've been a fan of **Aplós** for a while now, and I'd love to include it in this year's event. More and more of our guests are looking for a beautifully made drink that happens to be alcohol-free, and I can already picture one of the bartenders building a bright, celebratory spritz around **Aplós Arise** - something with real complexity from the botanicals, not just another mocktail. A crisp, botanical spritz is also a lovely light pairing with sushi, and a proper zero-proof option always ends up being one of the most talked-about pours of the night.

The audience is made up of **young professionals, hospitality creatives, and cocktail enthusiasts**, including a growing sober-curious crowd, so it's a group that genuinely appreciates discovering well-made products rather than simply trying another drink.

We're already lining up a handful of well-known spirits brands for this year's showcase, and we'd love to have **Aplós** alongside them as our functional, alcohol-free centerpiece.

Just to be clear, taking part is completely free - there's no sponsorship fee of any kind, only whatever product or support you're comfortable providing. If you'd be interested, we'd be glad to feature whatever makes the most sense from your perspective - whether that's a few bottles for the bartenders to build a dedicated zero-proof activation, branded glassware, merchandise, or anything else you'd like guests to experience. If there's a specific serve you'd love us to pour, we'd be excited to build something around it.

If you'd like, I'd be happy to send over a little more about the event, the bartenders, and what we have planned.

Thanks so much for taking the time to read this. We'd love the opportunity to introduce **Aplós** to our guests and hopefully create a few new fans along the way.""",
    },
    {
        "id": "italicus",
        "company": "Italicus",
        "real_to": "info@italicus.com",
        "subject": "Italicus x our NYC cocktail showcase (an aperitivo moment)",
        "body": """Hi Italicus team,

I hope you're doing well!

My name is Jackson Gold, and I'm one of the organizers of **Sips and Sushi**, a cocktail showcase we're hosting in New York featuring a group of incredibly talented up-and-coming bartenders - paired, as the name suggests, with fresh, chef-prepared sushi all evening.

This year will be the **fifth edition** of the showcase, and it's become one of our favorite events to put together. We'll have more than 100 guests spending the evening tasting original cocktails, pairing them with the sushi, meeting the bartenders behind the drinks, and discovering the products that make them special.

I've been a fan of **Italicus** for a while now, and I'd love to include it in this year's event. I can already picture one of the bartenders opening the evening with an **Italicus Rosolio di Bergamotto** spritz - that gorgeous bergamot-and-chamomile lift over prosecco is exactly the kind of elegant, aperitivo-hour welcome drink that sets the tone for a night like this. That citrus-and-floral lift plays beautifully against fresh sushi, and it happens to photograph gorgeously too, which our guests always love.

The audience is made up of **spirits enthusiasts, aperitivo lovers, and hospitality professionals**, so it's a group that genuinely appreciates discovering well-made products rather than simply trying another drink.

We're already lining up a handful of well-known spirits brands for this year's showcase, and we'd love to have **Italicus** alongside them to own the aperitivo moment.

Just to be clear, taking part is completely free - there's no sponsorship fee of any kind, only whatever product or support you're comfortable providing. If you'd be interested, we'd be glad to feature whatever makes the most sense from your perspective - whether that's a few bottles for the bartenders to build an aperitivo activation, branded glassware, bar tools, or anything else you'd like guests to experience. If there's a signature serve you'd love us to pour, we'd be excited to build the welcome cocktail around it.

If you'd like, I'd be happy to send over a little more about the event, the bartenders, and what we have planned.

Thanks so much for taking the time to read this. We'd love the opportunity to introduce **Italicus** to our guests and hopefully create a few new fans along the way.""",
    },
    {
        "id": "hamilton-rum",
        "company": "Hamilton Rum",
        "real_to": "info@caribbean-spirits.com",
        "subject": "Hamilton Rum x our NYC cocktail showcase (tiki, done right)",
        "body": """Hi Hamilton Rum team,

I hope you're doing well!

My name is Jackson Gold, and I'm one of the organizers of **Sips and Sushi**, a cocktail showcase we're hosting in New York featuring a group of incredibly talented up-and-coming bartenders - paired, as the name suggests, with fresh, chef-prepared sushi all evening.

This year will be the **fifth edition** of the showcase, and it's become one of our favorite events to put together. We'll have more than 100 guests spending the evening tasting original cocktails, pairing them with the sushi, meeting the bartenders behind the drinks, and discovering the products that make them special.

I've been a fan of **Hamilton Rum** for a while now - your rums are a bit of a bartender's secret weapon - and I'd love to include them in this year's event. I can already picture one of the bartenders building a proper Mai Tai or a Jungle Bird around **Hamilton Jamaican Pot Still Black**, letting that funky, high-ester character do the heavy lifting the way it's meant to. Our crowd really appreciates rums with a point of view, there's always a great story to tell about where these come from, and a well-balanced tiki drink is a surprisingly fun counterpoint to a plate of sushi.

The audience is made up of **craft cocktail enthusiasts, tiki lovers, and working bartenders**, so it's a group that genuinely appreciates discovering well-made products rather than simply trying another drink.

We're already lining up a handful of well-known spirits brands for this year's showcase, and we'd love to have **Hamilton Rum** alongside them to anchor the rum and tiki side of the night.

Just to be clear, taking part is completely free - there's no sponsorship fee of any kind, only whatever product or support you're comfortable providing. If you'd be interested, we'd be glad to feature whatever makes the most sense from your perspective - whether that's a few bottles across the range for the bartenders to work with, a little tiki/craft education for guests, branded glassware, or anything else you'd like people to experience. If there's a specific expression you'd love us to pour, we'd be excited to build a cocktail around it.

If you'd like, I'd be happy to send over a little more about the event, the bartenders, and what we have planned.

Thanks so much for taking the time to read this. We'd love the opportunity to introduce **Hamilton Rum** to our guests and hopefully create a few new fans along the way.""",
    },
    {
        "id": "dhos",
        "company": "Dhos",
        "real_to": "hello@dhosspirits.com",
        "subject": "Dhos x our NYC cocktail showcase (a real zero-proof menu)",
        "body": """Hi Dhos team,

I hope you're doing well!

My name is Jackson Gold, and I'm one of the organizers of **Sips and Sushi**, a cocktail showcase we're hosting in New York featuring a group of incredibly talented up-and-coming bartenders - paired, as the name suggests, with fresh, chef-prepared sushi all evening.

This year will be the **fifth edition** of the showcase, and it's become one of our favorite events to put together. We'll have more than 100 guests spending the evening tasting original cocktails, pairing them with the sushi, meeting the bartenders behind the drinks, and discovering the products that make them special.

I've been a fan of **Dhos** for a while now, and I'd love to include it in this year's event. I can already picture one of the bartenders building a zero-proof Negroni around **Dhos Bittersweet** - that bitter-orange backbone is exactly what makes an alcohol-free drink feel like a real cocktail instead of a compromise. A thoughtfully built zero-proof menu always ends up being one of the pleasant surprises of the evening, and a bittersweet, low-sugar pour is a great match for the clean flavors of sushi.

The audience is made up of **hospitality professionals, cocktail enthusiasts, and a growing sober-curious crowd**, so it's a group that genuinely appreciates discovering well-made products rather than simply trying another drink.

We're already lining up a handful of well-known spirits brands for this year's showcase, and we'd love to have **Dhos** alongside them to lead our alcohol-free menu.

Just to be clear, taking part is completely free - there's no sponsorship fee of any kind, only whatever product or support you're comfortable providing. If you'd be interested, we'd be glad to feature whatever makes the most sense from your perspective - whether that's a few bottles for the bartenders to build a dedicated zero-proof menu, branded glassware, merchandise, or anything else you'd like guests to experience. If there's a specific serve you'd love us to feature, we'd be excited to build something around it.

If you'd like, I'd be happy to send over a little more about the event, the bartenders, and what we have planned.

Thanks so much for taking the time to read this. We'd love the opportunity to introduce **Dhos** to our guests and hopefully create a few new fans along the way.""",
    },
]


def text_body(entry: dict) -> str:
    body = f"{entry['body']}\n\n{SIGNATURE}"
    # Plain-text version: drop the markdown bold markers.
    return body.replace("**", "")


def html_body(entry: dict, logo_cid: str | None = None) -> str:
    raw = f"{entry['body']}\n\n{SIGNATURE}"
    paragraphs = []
    for block in raw.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        block = (block.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        block = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", block)
        block = block.replace("\n", "<br>")
        paragraphs.append(f'<p style="margin:0 0 16px;">{block}</p>')
    inner = "\n".join(paragraphs)
    logo_html = (
        f'<div style="text-align:center;margin-bottom:18px;">'
        f'<img src="cid:{logo_cid}" alt="Sips and Sushi" '
        f'style="max-width:220px;height:auto;" /></div>'
        if logo_cid else ""
    )
    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:24px;background:#f4f4f5;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;
              padding:28px 32px;font-family:Helvetica,Arial,sans-serif;
              color:#1f2933;font-size:15px;line-height:1.6;">
    {logo_html}
    {inner}
  </div>
</body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Send 5 tailored test emails to yourself.")
    parser.add_argument("--to", default=config.FROM_EMAIL or config.SMTP_USER,
                        help="Recipient for all test emails (defaults to your own address).")
    parser.add_argument("--limit", type=int, default=0,
                        help="Only send the first N tailored emails (0 = all 5).")
    args = parser.parse_args()

    recipient = args.to.strip()
    if not recipient:
        sys.exit("No recipient. Pass --to you@example.com or set FROM_EMAIL in .env.")
    if not config.SMTP_USER or not config.SMTP_PASS:
        sys.exit("SMTP_USER / SMTP_PASS not set. Configure .env first.")

    smtp = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30)
    smtp.starttls()
    smtp.login(config.SMTP_USER, config.SMTP_PASS)

    logo_path = config.ROOT / "assets" / "sips_and_sushi_logo.png"
    logo_bytes = logo_path.read_bytes() if logo_path.exists() else None

    outbox = EMAILS[: args.limit] if args.limit else EMAILS
    sent = 0
    try:
        for entry in outbox:
            msg = EmailMessage()
            msg["From"] = formataddr((config.FROM_NAME, config.FROM_EMAIL))
            msg["To"] = recipient
            msg["Reply-To"] = config.REPLY_TO
            msg["Subject"] = f"[TEST -> {entry['company']} <{entry['real_to']}>] {entry['subject']}"
            msg["Message-ID"] = make_msgid(domain=config.FROM_EMAIL.split("@")[-1])
            msg.set_content(text_body(entry))

            logo_cid = None
            if logo_bytes:
                logo_cid = make_msgid(domain=config.FROM_EMAIL.split("@")[-1])[1:-1]
            msg.add_alternative(html_body(entry, logo_cid), subtype="html")

            if logo_bytes:
                html_part = msg.get_payload()[-1]
                html_part.add_related(
                    logo_bytes, maintype="image", subtype="png", cid=f"<{logo_cid}>",
                    filename="sips_and_sushi_logo.png",
                )
            smtp.send_message(msg)
            sent += 1
            print(f"[sent] {entry['company']} (would go to {entry['real_to']}) -> {recipient}")
            time.sleep(2)
    finally:
        smtp.quit()

    print(f"\nDone. {sent} tailored test emails delivered to {recipient}.")


if __name__ == "__main__":
    main()
