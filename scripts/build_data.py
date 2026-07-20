"""Parse the sponsorship spreadsheet into a normalized `data/prospects.json`.

Each prospect is classified as either `has_email` (a valid public email exists,
so it can be emailed automatically) or `route_only` (no email; must be reached
via phone/URL/other route). A stable `id` slug is assigned for later matching.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata

import openpyxl

import config

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Companies to exclude from outreach (e.g. brands referenced elsewhere / opted out).
# Matched by slugified company id.
EXCLUDE_IDS = {"moet-hennessy-usa"}

# Maps the spreadsheet headers to compact JSON keys.
COLUMN_MAP = {
    "Company": "company",
    "Parent Company": "parent_company",
    "Flagship Brands / Products": "brands",
    "Category": "category",
    "Sponsorship Likelihood": "likelihood",
    "Best Contact Route": "contact_route",
    "Public Email": "public_email",
    "Is This the Correct Sponsorship Route?": "route_confidence",
    "Official Contact / Source URL": "source_url",
    "Phone": "phone",
    "Distributor or Local Rep Needed?": "distributor_needed",
    "Best Ask": "best_ask",
    "Routing Notes": "routing_notes",
}


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value) or "prospect"


def clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def first_email(value: str) -> str:
    """Return the first valid email found in the cell, else empty string."""
    for token in re.split(r"[;,\s]+", value):
        token = token.strip().strip("<>").rstrip(".")
        if EMAIL_RE.match(token):
            return token.lower()
    return ""


def load_discovered_emails() -> dict:
    """Public emails found via research for companies that were route-only."""
    path = config.DATA_DIR / "discovered_emails.json"
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("emails", {})
    except Exception:  # noqa: BLE001
        return {}


def load_extra_prospects() -> list[dict]:
    """Additional prospects sourced via research (not in the spreadsheet)."""
    path = config.DATA_DIR / "extra_prospects.json"
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("prospects", [])
    except Exception:  # noqa: BLE001
        return []


def build() -> list[dict]:
    if not config.XLSX_PATH.exists():
        sys.exit(f"Spreadsheet not found: {config.XLSX_PATH}")

    discovered = load_discovered_emails()

    wb = openpyxl.load_workbook(config.XLSX_PATH, read_only=True, data_only=True)
    ws = wb["Sponsor Prospects"]
    rows = list(ws.iter_rows(values_only=True))
    header = [clean(h) for h in rows[0]]
    idx = {h: i for i, h in enumerate(header)}

    prospects: list[dict] = []
    seen_ids: set[str] = set()

    for raw in rows[1:]:
        if raw is None or all(c is None for c in raw):
            continue

        record: dict[str, str] = {}
        for col, key in COLUMN_MAP.items():
            record[key] = clean(raw[idx[col]]) if col in idx else ""

        if not record.get("company"):
            continue

        base_id = slugify(record["company"])
        if base_id in EXCLUDE_IDS:
            continue
        pid = base_id
        n = 2
        while pid in seen_ids:
            pid = f"{base_id}-{n}"
            n += 1
        seen_ids.add(pid)

        email = first_email(record.get("public_email", ""))
        record["id"] = pid
        # Merge in a researched public email if the spreadsheet had none.
        if not email and pid in discovered:
            email = discovered[pid].strip().lower()
            record["email_source"] = "researched"
        record["email"] = email
        record["status_class"] = "has_email" if email else "route_only"

        prospects.append(record)

    # Append researched prospects that aren't in the spreadsheet.
    for extra in load_extra_prospects():
        record = {key: clean(extra.get(key, "")) for key in COLUMN_MAP.values()}
        if not record.get("company"):
            continue
        base_id = slugify(record["company"])
        if base_id in EXCLUDE_IDS or base_id in seen_ids:
            continue
        seen_ids.add(base_id)

        email = first_email(record.get("public_email", ""))
        record["id"] = base_id
        record["email"] = email
        record["status_class"] = "has_email" if email else "route_only"
        record["email_source"] = "researched"
        if not record.get("contact_route"):
            record["contact_route"] = "Public contact email (researched)"
        if not record.get("routing_notes"):
            record["routing_notes"] = "Prospect and email sourced via research."
        prospects.append(record)

    return prospects


def main() -> None:
    prospects = build()
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.PROSPECTS_JSON, "w", encoding="utf-8") as fh:
        json.dump(prospects, fh, indent=2, ensure_ascii=False)

    has_email = sum(1 for p in prospects if p["status_class"] == "has_email")
    route_only = len(prospects) - has_email
    print(f"Wrote {len(prospects)} prospects -> {config.PROSPECTS_JSON}")
    print(f"  emailable: {has_email}  |  route-only: {route_only}")


if __name__ == "__main__":
    main()
