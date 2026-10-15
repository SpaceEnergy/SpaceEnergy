#!/usr/bin/env python3
"""
Render a neofetch-style info card SVG. Rows fade/slide in on a stagger.
Static profile facts live in INFO below; the stats rows are read from
data/contributions.json, so the daily workflow keeps them current.
STATIC=1 renders the final frame without animation.
"""
import html
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "info-card.svg")
STATIC = bool(os.environ.get("STATIC"))

INFO = [
    ("OS", "Linux (CachyOS)"),
    ("Age", "19"),
    ("Project", "SpaceThemes"),
    ("Wiki", "German Star Citizen Wiki"),
    ("Stack", "CSS · HTML · JavaScript · Shell"),
    ("Web", "spaceenergy.github.io"),
    ("Discord", "discord.gg/7Zv8Xz3Vzn"),
]

with open(DATA) as f:
    data = json.load(f)
STATS = [
    ("Contribs", f'{data["total_contributions"]:,} in the last year'),
    ("Streak", f'{data["current_streak"]} days (longest {data["longest_streak"]})'),
    ("Active", f'{data["active_days"]} days'),
]

W = 480
PAD = 24
LINE = 24
TITLEBAR_H = 30
BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK, ACCENT, KEY = "#7d8590", "#c9d1d9", "#8b8cff", "#a3a6ff"
PALETTE = ["#161b22", "#2b2d6e", "#4447b0", "#6a6ef0", "#a3a6ff", "#ff5f56", "#ffbd2e", "#27c93f"]

user = "spaceenergy@github"
lines = [("head", user), ("rule", "-" * len(user))]
lines += [("kv", kv) for kv in INFO]
lines.append(("blank", None))
lines += [("kv", kv) for kv in STATS]
lines.append(("blank", None))
lines.append(("palette", None))

top = TITLEBAR_H + PAD + 10
H = top + len(lines) * LINE + PAD

p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
     f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14">']
p.append("<style>@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"
         + ("" if STATIC else ".l{opacity:0;animation:in .5s ease-out forwards}")
         + "@media (prefers-reduced-motion){.l{animation:none;opacity:1}}</style>")
p.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>')
p.append(f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>')
p.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>')
p.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{20 + i*16}" cy="15" r="5" fill="{c}"/>')
p.append(f'<text x="{W/2}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">{user}: ~$ neofetch</text>')

for i, (kind, val) in enumerate(lines):
    y = top + i * LINE
    attrs = f'class="l" style="animation-delay:{0.3 + i*0.12:.2f}s"'
    if kind == "head":
        name, host = val.split("@")
        p.append(f'<text {attrs} x="{PAD}" y="{y}" font-weight="bold"><tspan fill="{ACCENT}">{name}</tspan>'
                 f'<tspan fill="{INK}">@</tspan><tspan fill="{ACCENT}">{host}</tspan></text>')
    elif kind == "rule":
        p.append(f'<text {attrs} x="{PAD}" y="{y}" fill="{MUTED}">{val}</text>')
    elif kind == "kv":
        k, v = val
        p.append(f'<text {attrs} xml:space="preserve" x="{PAD}" y="{y}"><tspan fill="{KEY}" font-weight="bold">{k}</tspan>'
                 f'<tspan fill="{MUTED}">: </tspan><tspan fill="{INK}">{html.escape(v)}</tspan></text>')
    elif kind == "palette":
        p.append(f'<g {attrs}>' + "".join(
            f'<rect x="{PAD + j*26}" y="{y-14}" width="24" height="16" rx="2" fill="{c}"/>'
            for j, c in enumerate(PALETTE)) + "</g>")

p.append("</svg>")
with open(OUT, "w") as f:
    f.write("".join(p))
print("wrote", OUT)
