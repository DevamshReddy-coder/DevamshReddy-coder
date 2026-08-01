#!/usr/bin/env python3
"""
render_heatmap_svg.py — draw data/contributions.json as the classic
53-week x 7-day calendar of rounded, colored boxes. Reveals once with a
diagonal, line-after-line slide-down (CSS keyframes that play on load, then
freeze — no looping), plus a legend and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py
Output:
    contrib-heatmap.svg
"""
import json
from datetime import datetime

SRC = "data/contributions.json"
OUT = "contrib-heatmap.svg"

PALETTE = [
    "#161b22",  # 0 - none
    "#0e4429",  # 1
    "#006d32",  # 2
    "#26a641",  # 3
    "#39d353",  # 4
    "#69f0a0",  # 5 - neon top end for the very best days
]

CELL = 12
GAP = 3
LEFT_PAD = 34   # room for weekday labels
TOP_PAD = 34    # room for month labels
RIGHT_PAD = 16
LEGEND_H = 26
FOOTER_H = 34

WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STAGGER = 0.012   # per diagonal (col+row) step
DUR = 0.32


def level_for(count, max_count):
    if count == 0:
        return 0
    if max_count <= 0:
        return 1
    # bucket into 5 non-zero levels, using rough quantiles so a handful of
    # huge days doesn't wash out everything else to "level 1"
    ratio = count / max_count
    if ratio > 0.8:
        return 5
    if ratio > 0.55:
        return 4
    if ratio > 0.3:
        return 3
    if ratio > 0.1:
        return 2
    return 1


def build_weeks(days):
    """Bucket days into GitHub-style weeks (columns), Sunday-first rows."""
    parsed = [
        {**d, "dt": datetime.strptime(d["date"], "%Y-%m-%d")}
        for d in days
    ]
    parsed.sort(key=lambda d: d["dt"])

    weeks = []
    current_week = [None] * 7
    for d in parsed:
        dow = (d["dt"].weekday() + 1) % 7  # convert Mon=0..Sun=6 -> Sun=0..Sat=6
        if dow == 0 and any(x is not None for x in current_week):
            weeks.append(current_week)
            current_week = [None] * 7
        current_week[dow] = d
    if any(x is not None for x in current_week):
        weeks.append(current_week)

    return weeks[-53:]  # keep at most 53 columns


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    payload = json.load(open(SRC))
    days = payload["days"]
    stats = payload["stats"]
    username = payload.get("username", "")

    max_count = max((d["count"] for d in days), default=0)
    weeks = build_weeks(days)
    n_weeks = len(weeks)

    grid_w = n_weeks * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    width = LEFT_PAD + grid_w + RIGHT_PAD
    height = TOP_PAD + grid_h + LEGEND_H + FOOTER_H

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Consolas, Menlo, \'Courier New\', monospace">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="transparent"/>')

    # keyframes: one per diagonal step (col+row), boxes slide down + fade in
    max_diag = n_weeks + 7
    style = ["<style>", ".box{opacity:0;}"]
    for diag in range(max_diag):
        style.append(f"""
        @keyframes slideIn{diag} {{
          from {{ opacity: 0; transform: translateY(-6px); }}
          to   {{ opacity: 1; transform: translateY(0); }}
        }}
        .diag{diag} {{
          animation: slideIn{diag} {DUR}s ease-out forwards;
          animation-delay: {diag * STAGGER:.3f}s;
        }}""")
    style.append("</style>")
    parts.append("".join(style))

    # month labels — placed above the first week-column that starts a new month
    seen_months = set()
    for wi, week in enumerate(weeks):
        first_day = next((d for d in week if d is not None), None)
        if not first_day:
            continue
        mkey = first_day["dt"].strftime("%Y-%m")
        if mkey not in seen_months:
            seen_months.add(mkey)
            x = LEFT_PAD + wi * (CELL + GAP)
            label = MONTH_NAMES[first_day["dt"].month - 1]
            parts.append(
                f'<text x="{x}" y="{TOP_PAD - 10}" font-size="10" fill="#8b949e">{label}</text>'
            )

    # weekday labels
    for dow, label in WEEKDAY_LABELS.items():
        y = TOP_PAD + dow * (CELL + GAP) + CELL - 2
        parts.append(f'<text x="0" y="{y}" font-size="10" fill="#8b949e">{label}</text>')

    # boxes
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = LEFT_PAD + wi * (CELL + GAP)
            y = TOP_PAD + di * (CELL + GAP)
            if day is None:
                continue
            level = level_for(day["count"], max_count)
            color = PALETTE[level]
            diag = wi + di
            title = f"{day['count']} contributions on {day['date']}"
            parts.append(
                f'<rect class="box diag{diag}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" fill="{color}"><title>{esc(title)}</title></rect>'
            )

    # legend
    legend_y = TOP_PAD + grid_h + 20
    parts.append(f'<text x="{LEFT_PAD}" y="{legend_y}" font-size="10" fill="#8b949e">Less</text>')
    lx = LEFT_PAD + 32
    for lvl, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx}" y="{legend_y-9}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
        lx += CELL + GAP
    parts.append(f'<text x="{lx+4}" y="{legend_y}" font-size="10" fill="#8b949e">More</text>')

    # stats footer
    footer_y = legend_y + FOOTER_H - 8
    total = stats.get("total_last_year", 0)
    longest = stats.get("longest_streak", 0)
    current = stats.get("current_streak", 0)
    footer_text = f"{total:,} contributions in the last year  ·  longest streak {longest}d  ·  current streak {current}d"
    parts.append(
        f'<text x="{LEFT_PAD}" y="{footer_y}" font-size="11" fill="#c9d1d9">{esc(footer_text)}</text>'
    )

    parts.append("</svg>")

    with open(OUT, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {OUT}  ({n_weeks} weeks x 7 days, {width}x{height}px)")


if __name__ == "__main__":
    main()
