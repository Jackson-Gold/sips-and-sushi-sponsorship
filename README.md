# Cocktail Event Sponsorship Outreach

A small pipeline that sends personalized sponsorship-request emails to a list of
beverage companies and publishes a live statistics dashboard on **GitHub Pages**,
refreshed automatically by **GitHub Actions**.

- **100 prospects** from `data/cocktail_event_sponsorship_contacts_100_companies.xlsx`
  (66 have a public email and can be emailed; 34 are "route-only" and are surfaced
  as an action list instead).
- Personalized emails (plain text + HTML) tailored by sponsorship likelihood.
- Static dashboard: KPIs, funnel, breakdowns by category / likelihood / ask,
  activity timeline, and a searchable prospect table.
- Reply tracking via IMAP, run on a schedule in Actions.

## How it works

```
xlsx ──> build_data.py ──> data/prospects.json
                                  │
        send_emails.py (SMTP) ────┼──> data/sends.json
        track_replies.py (IMAP) ──┼──> data/status.json
                                  ▼
                           aggregate.py ──> docs/data/stats.json ──> GitHub Pages
```

Open/click pixel tracking is intentionally **not** included: GitHub Pages is a
static host with no server to log pixel hits. Reply tracking via IMAP is the
equivalent signal and runs entirely inside Actions. (See "Extending" below.)

## Local setup

```bash
pip install -r requirements.txt
cp .env.example .env      # fill in SMTP/IMAP creds + event/organizer details
python scripts/build_data.py          # regenerate prospects.json from the xlsx
python scripts/send_emails.py --dry-run --limit 5   # writes previews/*.eml (no send)
python scripts/aggregate.py           # regenerate docs/data/stats.json
```

Preview the dashboard locally:

```bash
python -m http.server 8000 --directory docs
# open http://localhost:8000
```

### Sending for real

```bash
python scripts/send_emails.py --limit 10     # sends up to 10, throttled
python scripts/track_replies.py              # scan inbox for replies
python scripts/aggregate.py                  # refresh the dashboard data
```

Useful flags for `send_emails.py`: `--dry-run`, `--limit N`, `--resend`,
`--only id1,id2`.

## Deploying on GitHub

1. Create a repo and push this project.
2. **Settings -> Pages**: set *Source* = "GitHub Actions".
3. Add **Actions secrets** (Settings -> Secrets and variables -> Actions -> Secrets):
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`, `REPLY_TO`
   - `IMAP_HOST`, `IMAP_PORT`, `IMAP_USER`, `IMAP_PASS`, `IMAP_FOLDER`
4. Add **Actions variables** (same page -> Variables) for non-secret content:
   - `FROM_NAME`, `SEND_THROTTLE_SECONDS`
   - `EVENT_NAME`, `EVENT_DATE`, `EVENT_CITY`, `EVENT_VENUE`, `EVENT_ATTENDANCE`,
     `EVENT_AUDIENCE`, `EVENT_WEBSITE`
   - `ORGANIZER_NAME`, `ORGANIZER_TITLE`, `ORGANIZER_ORG`, `ORGANIZER_PHONE`,
     `PHYSICAL_ADDRESS`, `OPT_OUT_EMAIL`

> Gmail / Google Workspace: enable 2FA and create an **App Password**; use it for
> both `SMTP_PASS` and `IMAP_PASS`.

### Workflows

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `deploy.yml` | push to `main` (docs/**), manual | Publishes `docs/` to GitHub Pages |
| `send.yml` | manual dispatch | Sends emails in batches (defaults to dry-run); commits `sends.json` + stats |
| `track.yml` | every 6h + manual | IMAP reply scan, rebuilds stats, commits (which redeploys Pages) |

Run `send.yml` first with **dry run = true** to download the `email-previews`
artifact and eyeball the messages. Then re-run with dry run = false and a small
`limit` to start sending.

## Compliance (read before sending)

This tool sends commercial email. To stay on the right side of **CAN-SPAM** (US)
and similar laws:

- Every email includes a real physical mailing address and a one-line opt-out
  (`OPT_OUT_EMAIL`) plus a `List-Unsubscribe` header. Set these to real values.
- Honor opt-outs promptly. Use `--only`/exclusion to avoid re-contacting anyone
  who asks to be removed.
- Keep the throttle (`SEND_THROTTLE_SECONDS`) reasonable to protect sender
  reputation and stay within provider limits.
- No email addresses are invented — route-only companies are never emailed.

## Project layout

```
data/
  cocktail_event_sponsorship_contacts_100_companies.xlsx   # source list
  prospects.json     # normalized prospects (generated)
  sends.json         # per-company send log (generated)
  status.json        # per-company reply state (generated)
scripts/
  config.py          # env + paths + event/organizer context
  build_data.py      # xlsx -> prospects.json
  send_emails.py     # render + send (SMTP), dry-run previews
  track_replies.py   # IMAP reply matching
  aggregate.py       # -> docs/data/stats.json
templates/           # Jinja2 subject + text/html bodies
docs/                # static dashboard (served by GitHub Pages)
.github/workflows/   # deploy / send / track
```

## Extending

- **Open/click tracking**: add a tiny serverless endpoint (Cloudflare Worker,
  Vercel function) that logs a pixel/redirect hit, then feed those counts into
  `aggregate.py`. Not possible on static Pages alone.
- **Email API instead of SMTP**: swap the `smtplib` block in `send_emails.py`
  for a provider SDK (Resend/SendGrid/Postmark); the rest is unchanged.
