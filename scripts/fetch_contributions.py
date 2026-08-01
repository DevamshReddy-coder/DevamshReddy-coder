#!/usr/bin/env python3
"""
fetch_contributions.py — scrape a GitHub user's public contribution
calendar with no token / no GraphQL API. GitHub serves the calendar as an
HTML fragment at https://github.com/users/<username>/contributions — the
same markup the profile page itself uses.

Usage:
    python scripts/fetch_contributions.py
Output:
    data/contributions.json
"""
import json
import os
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "DevamshReddy-coder")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = os.path.join("data", "contributions.json")


def fetch_days():
    headers = {"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}
    resp = requests.get(URL, headers=headers, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    # GitHub renders each day as a <td> (older markup) or <rect>/<td> depending
    # on version; the tds carry data-date and either data-level or a
    # data-count-derived class. We handle both shapes defensively.
    cells = soup.select("td.ContributionCalendar-day") or soup.select("[data-date]")
    for cell in cells:
        date_str = cell.get("data-date")
        if not date_str:
            continue
        level = cell.get("data-level")
        tooltip_id = cell.get("id")
        count = 0
        if tooltip_id:
            tip = soup.find("tool-tip", attrs={"for": tooltip_id})
            if tip and tip.text:
                text = tip.text.strip()
                first_tok = text.split()[0].replace(",", "")
                if first_tok.isdigit():
                    count = int(first_tok)
                elif text.lower().startswith("no contributions"):
                    count = 0
        days.append({
            "date": date_str,
            "count": count,
            "level": int(level) if level is not None else None,
        })

    days.sort(key=lambda d: d["date"])
    return days


def derive_stats(days):
    total = sum(d["count"] for d in days)

    # streaks
    longest = current = 0
    run = 0
    for d in days:
        if d["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    # current streak = trailing run ending today (or the last day we have data for)
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = {}
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] = monthly.get(month_key, 0) + d["count"]

    return {
        "total_last_year": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly": monthly,
    }


def main():
    try:
        days = fetch_days()
    except Exception as e:
        print(f"fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not days:
        print("no contribution cells parsed — GitHub markup may have changed", file=sys.stderr)
        sys.exit(1)

    stats = derive_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    os.makedirs("data", exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"wrote {OUT}  ({len(days)} days, {stats['total_last_year']} contributions)")


if __name__ == "__main__":
    main()
