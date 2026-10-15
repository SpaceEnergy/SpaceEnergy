#!/usr/bin/env python3
"""
One-time: turn an image into a monochrome ASCII-art SVG that "prints" itself
row by row (SMIL clip wipe + riding cursor), then holds.

  python scripts/make_ascii_svg.py [source.png] [out.svg]

Defaults to the GitHub avatar (assets/avatar.png). KEY selects how pixel
"ink" is measured:
  KEY=blue   (default) only the blue/purple logo counts, the space background
             is dropped and replaced by a generated ASCII starfield
  KEY=light  bright pixels are dense (any image on a dark background)
  KEY=dark   dark pixels are dense (a photo on a white background)
STATIC=1 renders the final frame without animation.
"""
import html
import os
import random
import sys

from PIL import Image, ImageChops

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "avatar.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "ascii-art.svg")
STATIC = bool(os.environ.get("STATIC"))
KEY = os.environ.get("KEY", "blue")

# canvas matches info-card.svg's aspect so both sit at equal height in the README
W, H = 384, 448
COLS = int(os.environ.get("COLS", 48))
PAD = 20
ART_W = W - PAD * 2
CELL_W = ART_W / COLS
CELL_H = CELL_W * 15 / 8  # monospace glyphs are ~1:1.875
RAMP = " .:-=+*#%@"       # sparse -> dense
STARS = ".....·+*"

TITLEBAR_H = 30
STATUS_H = 40
BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK, STAR = "#7d8590", "#8b8cff", "#4a5160"

art_top = TITLEBAR_H + 10
ROWS = int((H - art_top - STATUS_H - 10) / CELL_H)

# ---- sample the image ------------------------------------------------------
def ink(r, g, b):
    if KEY == "blue":
        return max(0.0, min(1.0, (b - r - 50) / 80))
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return lum if KEY == "light" else 1 - lum


im = Image.open(SRC).convert("RGB")
if KEY == "blue":
    # crop to the logo so it fills the canvas instead of the empty sky
    r_, _, b_ = im.split()
    mask = ImageChops.subtract(b_, r_).point(lambda d: 255 if d > 60 else 0)
    l, t, r, b = mask.getbbox()
    m = (r - l) // 12
    im = im.crop((l - m, t - m, r + m, b + m))
logo_rows = min(ROWS, round(COLS * im.height / im.width * CELL_W / CELL_H))
im = im.resize((COLS, logo_rows), Image.LANCZOS)
px = im.load()

rnd = random.Random(42)
offset = (ROWS - logo_rows) // 2
grid = []  # list of rows, each a list of (char, is_star)
for y in range(ROWS):
    row = []
    for x in range(COLS):
        ly = y - offset
        v = ink(*px[x, ly]) if 0 <= ly < logo_rows else 0
        if v > 0.12:
            row.append((RAMP[min(len(RAMP) - 1, 1 + int(v * (len(RAMP) - 1)))], False))
        elif rnd.random() < 0.035:
            row.append((rnd.choice(STARS), True))
        else:
            row.append((" ", False))
    grid.append(row)

# ---- assemble SVG ----------------------------------------------------------
ROW_DUR = 4.0 / ROWS  # whole image prints in ~4s
p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
     f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
p.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>')
p.append(f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>')
p.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>')
p.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{c}"/>')
p.append(f'<text x="{W/2 + 20}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
         f'spaceenergy@github: ~$ ./logo.sh</text>')

font = CELL_H * 0.9
for i, row in enumerate(grid):
    row_y = art_top + i * CELL_H
    # stars and logo glyphs go in separate colored tspans; each run is padded
    # to full width with spaces so textLength keeps the columns aligned
    spans = "".join(
        f'<tspan fill="{STAR if star else INK}">{html.escape(ch)}</tspan>' if ch != " " else " "
        for ch, star in row)
    text = (f'<text xml:space="preserve" x="{PAD}" y="{row_y + CELL_H*0.78:.1f}" font-size="{font:.1f}" '
            f'textLength="{ART_W}" lengthAdjust="spacing">{spans}</text>')
    if STATIC:
        p.append(text)
        continue
    begin = i * ROW_DUR
    p.append(f'<clipPath id="r{i}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H:.2f}" width="0">'
             f'<animate attributeName="width" from="0" to="{ART_W}" begin="{begin:.3f}s" '
             f'dur="{ROW_DUR:.3f}s" fill="freeze"/></rect></clipPath>')
    p.append(f'<g clip-path="url(#r{i})">{text}</g>')
    p.append(f'<rect y="{row_y:.1f}" width="{CELL_W:.2f}" height="{CELL_H:.2f}" fill="{INK}" opacity="0">'
             f'<animate attributeName="x" from="{PAD}" to="{PAD + ART_W}" begin="{begin:.3f}s" '
             f'dur="{ROW_DUR:.3f}s" fill="freeze"/>'
             f'<set attributeName="opacity" to=".9" begin="{begin:.3f}s"/>'
             f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.3f}s"/></rect>')

# status bar with blinking cursor
sl = H - STATUS_H
sy = sl + 25
prompt, name = "~$ whoami ", "SpaceEnergy"
p.append(f'<line x1="0" y1="{sl}" x2="{W}" y2="{sl}" stroke="{FRAME}"/>')
p.append(f'<text xml:space="preserve" x="{PAD}" y="{sy}" fill="{MUTED}" font-size="13">{prompt}<tspan fill="{INK}">{name}</tspan></text>')
p.append(f'<rect x="{PAD + (len(prompt) + len(name) + 1) * 13 * 0.6:.1f}" y="{sy - 11}" width="8" height="14" fill="{INK}">'
         f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.51;1" dur="1s" repeatCount="indefinite"/></rect>')
p.append("</svg>")

with open(OUT, "w") as f:
    f.write("".join(p))
print(f"wrote {OUT}: {COLS}x{ROWS} chars, {W}x{H}px")
