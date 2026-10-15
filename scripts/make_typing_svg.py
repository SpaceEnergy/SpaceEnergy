#!/usr/bin/env python3
"""
One-time: a terminal line that types and deletes rotating phrases forever
(SMIL, discrete steps per character). Edit PHRASES and re-run.
STATIC=1 shows the first phrase fully typed.
"""
import html
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "typing.svg")
STATIC = bool(os.environ.get("STATIC"))

PHRASES = [
    "building SpaceTheme for Steam, Discord & more",
    "making Steam libraries look out of this world",
    "working on the German Star Citizen Wiki",
    "writing way too much CSS",
    "exploring the 'verse, one commit at a time",
]
PROMPT = "~$ "
W, H = 860, 52
SIZE = 18
CW = SIZE * 0.6          # monospace advance; textLength pins it exactly
TYPE, DELETE, HOLD, GAP = 0.055, 0.025, 1.8, 0.4
INK, ACCENT = "#c9d1d9", "#8b8cff"
BG, FRAME = "#0d1117", "#30363d"

# timeline: each phrase types, holds, deletes, pauses
spans, t = [], 0.0
for ph in PHRASES:
    start = t
    t += len(ph) * TYPE + HOLD + len(ph) * DELETE + GAP
    spans.append((ph, start))
T = t

prefix_w = len(PROMPT) * CW
total_w = len(PROMPT) * CW + max(len(ph) for ph in PHRASES) * CW + 12
x0 = (W - total_w) / 2
tx = x0 + prefix_w

p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
     f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="{SIZE}">']
p.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{FRAME}"/>')
p.append(f'<text x="{x0:.1f}" y="32" fill="{ACCENT}" font-weight="bold" textLength="{prefix_w - CW:.1f}">~$</text>')

timeline = []  # (time, phrase index, typed chars) for every step of the loop
for i, (ph, start) in enumerate(spans):
    n = len(ph)
    timeline += [(start + k * TYPE, i, k) for k in range(1, n + 1)]
    hold_end = start + n * TYPE + HOLD
    timeline += [(hold_end + k * DELETE, i, n - k) for k in range(1, n + 1)]
timeline = [(0.0, 0, 0)] + timeline


def anim(attr, values):
    keys = ";".join(f"{t / T:.5f}" for t, _, _ in timeline)
    return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{T:.2f}s" repeatCount="indefinite" '
            f'keyTimes="{keys}" values="{";".join(values)}"/>')


for i, (ph, _) in enumerate(spans):
    n = len(ph)
    width = n * CW if (STATIC and i == 0) else 0
    p.append(f'<clipPath id="c{i}"><rect x="{tx:.1f}" y="0" height="{H}" width="{width:.1f}">')
    if not STATIC:
        p.append(anim("width", [f"{k * CW:.1f}" if j == i else "0" for _, j, k in timeline]))
    p.append("</rect></clipPath>")
    p.append(f'<text clip-path="url(#c{i})" x="{tx:.1f}" y="32" fill="{INK}" '
             f'textLength="{n * CW:.1f}" lengthAdjust="spacing">{html.escape(ph)}</text>')

# cursor rides the end of the typed text
cx = tx + (len(PHRASES[0]) * CW if STATIC else 0) + 2
p.append(f'<rect x="{cx:.1f}" y="16" width="{CW * 0.9:.1f}" height="21" fill="{ACCENT}">')
if not STATIC:
    p.append(anim("x", [f"{tx + k * CW + 2:.1f}" for _, _, k in timeline]))
p.append('<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.51;1" dur="1s" repeatCount="indefinite"/>')
p.append("</rect></svg>")

with open(OUT, "w") as f:
    f.write("".join(p))
print(f"wrote {OUT}: {len(PHRASES)} phrases, {T:.1f}s loop")
