"""Join prospects + sends + replies into `docs/data/stats.json` for the dashboard.

Produces KPI totals, breakdowns by category / likelihood / best-ask, a daily
timeline, a funnel, and a per-company table. This file is the single data source
the static dashboard reads, so it is safe to commit and publish via Pages.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone

import config

# Company-level status precedence (highest wins).
STATUS_ORDER = ["replied", "failed", "sent", "skipped", "pending"]


def load_json(path, default):
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def date_of(iso: str) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).astimezone(timezone.utc).date().isoformat()
    except ValueError:
        return iso[:10]


def company_status(prospect, send, replied) -> str:
    if replied:
        return "replied"
    if send:
        s = send.get("status")
        if s == "failed":
            return "failed"
        if s == "sent":
            return "sent"
        if s == "skipped":
            return "skipped"
    if prospect["status_class"] == "route_only":
        return "skipped"
    return "pending"


def main() -> None:
    prospects = load_json(config.PROSPECTS_JSON, [])
    sends = load_json(config.SENDS_JSON, {})
    status = load_json(config.STATUS_JSON, {})

    companies = []
    kpi = Counter()
    by_category = defaultdict(lambda: Counter())
    by_likelihood = defaultdict(lambda: Counter())
    ask_counter = Counter()
    timeline_sent = Counter()
    timeline_reply = Counter()

    for p in prospects:
        pid = p["id"]
        send = sends.get(pid)
        rep = status.get(pid)
        cstatus = company_status(p, send, rep)

        kpi[cstatus] += 1
        kpi["total"] += 1
        if p["status_class"] == "has_email":
            kpi["emailable"] += 1
        else:
            kpi["route_only"] += 1

        cat = p.get("category") or "Uncategorized"
        like = p.get("likelihood") or "Unknown"
        by_category[cat][cstatus] += 1
        by_category[cat]["total"] += 1
        by_likelihood[like][cstatus] += 1
        by_likelihood[like]["total"] += 1

        for token in (p.get("best_ask") or "").split(";"):
            token = token.strip().lower()
            if token:
                ask_counter[token] += 1

        if send and send.get("status") == "sent":
            timeline_sent[date_of(send.get("timestamp", ""))] += 1
        if rep:
            timeline_reply[date_of(rep.get("first_reply_at", ""))] += 1

        companies.append({
            "id": pid,
            "company": p["company"],
            "parent_company": p.get("parent_company", ""),
            "brands": p.get("brands", ""),
            "category": cat,
            "likelihood": like,
            "best_ask": p.get("best_ask", ""),
            "email": p.get("email", ""),
            "status": cstatus,
            "contact_route": p.get("contact_route", ""),
            "phone": p.get("phone", ""),
            "source_url": p.get("source_url", ""),
            "routing_notes": p.get("routing_notes", ""),
            "subject": send.get("subject", "") if send else "",
            "message_id": send.get("message_id", "") if send else "",
            "send_reason": send.get("reason", "") if send else "",
            "sent_at": send.get("timestamp", "") if send else "",
            "reply_count": rep.get("reply_count", 0) if rep else 0,
            "reply_from": rep.get("last_from", "") if rep else "",
            "reply_subject": rep.get("last_subject", "") if rep else "",
            "reply_at": rep.get("first_reply_at", "") if rep else "",
        })

    sent = kpi.get("sent", 0)
    replied = kpi.get("replied", 0)
    reply_rate = round(replied / sent * 100, 1) if sent else 0.0

    def rows(mapping):
        out = []
        for label, c in sorted(mapping.items(), key=lambda kv: -kv[1]["total"]):
            out.append({
                "label": label,
                "total": c["total"],
                "sent": c.get("sent", 0),
                "replied": c.get("replied", 0),
                "skipped": c.get("skipped", 0),
                "pending": c.get("pending", 0),
                "failed": c.get("failed", 0),
            })
        return out

    all_dates = sorted(set(timeline_sent) | set(timeline_reply))
    timeline = [
        {"date": d, "sent": timeline_sent.get(d, 0), "replies": timeline_reply.get(d, 0)}
        for d in all_dates if d
    ]

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "event": config.EVENT,
        "kpis": {
            "total": kpi.get("total", 0),
            "emailable": kpi.get("emailable", 0),
            "route_only": kpi.get("route_only", 0),
            "sent": sent,
            "replied": replied,
            "skipped": kpi.get("skipped", 0),
            "failed": kpi.get("failed", 0),
            "pending": kpi.get("pending", 0),
            "reply_rate": reply_rate,
        },
        "by_category": rows(by_category),
        "by_likelihood": rows(by_likelihood),
        "by_best_ask": [
            {"label": k, "count": v}
            for k, v in ask_counter.most_common(12)
        ],
        "timeline": timeline,
        "funnel": {
            "prospects": kpi.get("total", 0),
            "emailable": kpi.get("emailable", 0),
            "sent": sent,
            "replied": replied,
        },
        "companies": companies,
    }

    save_json(config.STATS_JSON, stats)
    print(f"Wrote stats -> {config.STATS_JSON}")
    print(f"  total={stats['kpis']['total']} sent={sent} replied={replied} "
          f"skipped={stats['kpis']['skipped']} pending={stats['kpis']['pending']}")


if __name__ == "__main__":
    main()
