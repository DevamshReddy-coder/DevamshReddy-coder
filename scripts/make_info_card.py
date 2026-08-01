#!/usr/bin/env python3
"""
make_info_card.py — hand-authored neofetch-style SVG panel: a title bar,
then colored key/value rows. Each line fades and slides in on a short
stagger. Set STATIC=1 to emit a frozen frame (useful for Quick Look/local
previews where nothing animates).

Usage:
    python scripts/make_info_card.py
Output:
    info-card.svg
"""
import os

OUT = "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

USER = "DevamshReddy-coder@github"
TITLE = "CHUDI SAI DEVAMSH REDDY"

# key, value, accent color (GitHub-dark-ish palette)
ROWS = [
    ("Now",        "Backend systems in Java, Spring Boot & Node.js", "#79c0ff"),
    ("Focus",      "APIs, performance, clean architecture",          "#79c0ff"),
    ("Learning",   "System design & production-grade scalability",   "#d2a8ff"),
    ("Open to",    "Backend / REST APIs / open-source collab",       "#7ee787"),
    ("Ask me",     "API design, databases, debugging at scale",      "#7ee787"),
    ("Stack",      "Java · JavaScript · Python · Node · Express",    "#ffa657"),
    ("Data",       "MySQL · PostgreSQL · MongoDB · SQLite",          "#ffa657"),
    ("Fun fact",   "Optimizes code as much as competitive cricket",  "#f778ba"),
]

WIDTH = 490
PAD_X = 22
PAD_TOP = 20
TITLEBAR_H = 34
ROW_H = 27
KEY_W = 82
FONT_MONO = "Consolas, Menlo, 'Courier New', monospace"

BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT_MAIN = "#c9d1d9"
TEXT_DIM = "#8b949e"

STAGGER = 0.11
DUR = 0.35


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main():
    n = len(ROWS)
    body_h = n * ROW_H + 14
    height = TITLEBAR_H + PAD_TOP + body_h + 20

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="{FONT_MONO}">'
    )

    # panel background + border, rounded like a terminal window
    parts.append(
        f'<rect x="1" y="1" width="{WIDTH-2}" height="{height-2}" rx="10" '
        f'fill="{PANEL}" stroke="{BORDER}"/>'
    )

    # title bar with traffic-light dots
    parts.append(f'<rect x="1" y="1" width="{WIDTH-2}" height="{TITLEBAR_H}" rx="10" fill="#161b22"/>')
    parts.append(f'<rect x="1" y="{TITLEBAR_H-8}" width="{WIDTH-2}" height="8" fill="{PANEL}"/>')
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{22 + i*18}" cy="{TITLEBAR_H/2}" r="5.5" fill="{c}"/>')
    parts.append(
        f'<text x="{WIDTH/2}" y="{TITLEBAR_H/2 + 4}" text-anchor="middle" '
        f'font-size="12" fill="{TEXT_DIM}">{esc(USER)}</text>'
    )

    style_lines = ["<style>"]
    style_lines.append(f"text{{fill:{TEXT_MAIN};}}")
    if not STATIC:
        for i in range(n + 1):  # +1 for the title line itself
            style_lines.append(f"""
            @keyframes fadeIn{i} {{
              from {{ opacity: 0; transform: translateX(-6px); }}
              to   {{ opacity: 1; transform: translateX(0); }}
            }}
            .line{i} {{
              opacity: 0;
              animation: fadeIn{i} {DUR}s ease-out forwards;
              animation-delay: {i * STAGGER:.3f}s;
            }}""")
    style_lines.append("</style>")
    parts.append("".join(style_lines))

    y = TITLEBAR_H + PAD_TOP + 6
    cls0 = "" if STATIC else 'class="line0"'
    parts.append(
        f'<text {cls0} x="{PAD_X}" y="{y}" font-size="15" font-weight="bold" '
        f'fill="#58a6ff">{esc(TITLE)}</text>'
    )
    y += 10
    parts.append(f'<line x1="{PAD_X}" y1="{y}" x2="{WIDTH-PAD_X}" y2="{y}" stroke="{BORDER}"/>')
    y += 22

    for i, (key, val, color) in enumerate(ROWS, start=1):
        cls = "" if STATIC else f'class="line{i}"'
        parts.append(
            f'<text {cls} x="{PAD_X}" y="{y}" font-size="13" font-weight="bold" '
            f'fill="{color}">{esc(key)}</text>'
        )
        parts.append(
            f'<text {cls} x="{PAD_X + KEY_W}" y="{y}" font-size="12.5" '
            f'fill="{TEXT_MAIN}">{esc(val)}</text>'
        )
        y += ROW_H

    parts.append("</svg>")

    with open(OUT, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {OUT}{' (static)' if STATIC else ''}")


if __name__ == "__main__":
    main()
