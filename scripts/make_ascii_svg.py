#!/usr/bin/env python3
"""
make_ascii_svg.py — downsample prepped.png to a character grid and emit a
self-typing, monochrome ASCII-art SVG.

Each row wipes in left-to-right (a small block cursor rides the wipe edge),
staggered top to bottom. The portrait prints once and freezes — no looping.
Because the animation is plain SMIL/CSS inside the SVG, GitHub renders it.

Usage:
    python scripts/make_ascii_svg.py
Output:
    avi-ascii.svg
"""
import numpy as np
from PIL import Image

SRC = "prepped.png"
OUT = "avi-ascii.svg"

# Character grid size. ~2:1 char aspect ratio is baked into CELL_W/CELL_H below.
COLS = 100
ROWS = 62

# bright (sparse) -> dark (dense); leading space clears background to nothing
RAMP = " .`:-=+*cs#%@"

FONT_SIZE = 9
CELL_W = 5.6
CELL_H = 11.0
FILL = "#8b949e"          # monochrome light-gray, matches GitHub dark-mode text
BG = "transparent"
ROW_STAGGER = 0.045        # seconds between successive rows starting
WIPE_DURATION = 0.38       # seconds for a single row's left-to-right reveal


def load_grid():
    img = Image.open(SRC).convert("L")
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float32) / 255.0  # 0=black 1=white
    return arr


def brightness_to_char(v: float) -> str:
    # v: 0 (black/dense) -> 1 (white/sparse)
    idx = int(round((1 - v) * (len(RAMP) - 1)))
    idx = max(0, min(len(RAMP) - 1, idx))
    return RAMP[idx]


def row_to_string(row: np.ndarray) -> str:
    return "".join(brightness_to_char(v) for v in row)


def esc(c: str) -> str:
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;"}.get(c, c)


def main():
    arr = load_grid()
    lines = [row_to_string(arr[r]) for r in range(ROWS)]

    width = COLS * CELL_W + 20
    height = ROWS * CELL_H + 20

    svg_parts = []
    svg_parts.append(
        f'<svg viewBox="0 0 {width:.1f} {height:.1f}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Consolas, Menlo, \'Courier New\', monospace" font-size="{FONT_SIZE}">'
    )
    svg_parts.append(f'<rect width="100%" height="100%" fill="{BG}"/>')

    style = ["<style>"]
    style.append("text{fill:%s; white-space:pre;}" % FILL)
    for r in range(ROWS):
        style.append(f"""
        @keyframes wipeRow{r} {{
          from {{ clip-path: inset(0 100% 0 0); }}
          to   {{ clip-path: inset(0 0 0 0); }}
        }}
        .row{r} {{
          animation: wipeRow{r} {WIPE_DURATION}s steps(30, end) forwards;
          animation-delay: {r * ROW_STAGGER:.3f}s;
          clip-path: inset(0 100% 0 0);
        }}""")
    style.append("</style>")
    svg_parts.append("".join(style))

    for r, line in enumerate(lines):
        y = 14 + r * CELL_H
        escaped = "".join(esc(c) for c in line)
        # xml:space preserve keeps leading/trailing ramp spaces (the "blank" glyphs) intact
        svg_parts.append(
            f'<text class="row{r}" x="10" y="{y:.1f}" xml:space="preserve">{escaped}</text>'
        )

    svg_parts.append("</svg>")

    with open(OUT, "w") as f:
        f.write("\n".join(svg_parts))
    print(f"wrote {OUT}  ({COLS}x{ROWS} chars, {width:.0f}x{height:.0f}px)")


if __name__ == "__main__":
    main()
