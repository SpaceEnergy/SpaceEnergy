#!/usr/bin/env python3
"""
Render the recent public activity from data/stats.json as a terminal log
(`tail activity.log`). Lines print one after another, then a cursor blinks.
STATIC=1 renders the final frame without animation.
"""
import datetime
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "activity.svg")
STATIC = bool(os.environ.get("STATIC"))

with open(os.path.join(ROOT, "data", "stats.json")) as f:
    data = json.load(f)
events = data.get("activity", [])
now = datetime.datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))

W = 860
PAD = 20
TB = 30
LINE = 26
BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK, ACCENT = "#7d8590", "#c9d1d9", "#8b8cff"
KINDS = {  # label, color
    "push": ("push", "#7ee0b5"),
    "release": ("release", "#f2c46d"),
    "pr": ("pr", "#8b8cff"),
    "issue": ("issue", "#ff8f6b"),
    "comment": ("comment", "#7d8590"),
    "create": ("new", "#a3a6ff"),
    "star": ("star", "#f2c46d"),
    "fork": ("fork", "#6a6ef0"),
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ago(ts):
    secs = (now - datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))).total_seconds()
    for unit, n in (("d", 86400), ("h", 3600), ("m", 60)):
        if secs >= n:
            return f"{int(secs // n)}{unit} ago"
    return "just now"


top = TB + 34
H = top + len(events) * LINE + 18
repo_w = min(40, max((len(e["repo"]) for e in events), default=0))

p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
     f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="13">']
p.append("<style>@keyframes in{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}"
         "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
         + ("" if STATIC else ".l{opacity:0;animation:in .35s ease-out forwards}")
         + ".c{animation:blink 1s step-end infinite}"
         "@media (prefers-reduced-motion){.l{animation:none;opacity:1}}</style>")
p.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>')
p.append(f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>')
p.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>')
p.append(f'<line x1="0" y1="{TB}" x2="{W}" y2="{TB}" stroke="{FRAME}"/>')
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{20 + i*16}" cy="15" r="5" fill="{c}"/>')
p.append(f'<text x="{W/2}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">'
         f'{data["username"].lower()}@github: ~$ tail activity.log</text>')

for i, e in enumerate(events):
    y = top + i * LINE
    label, color = KINDS.get(e["kind"], (e["kind"], MUTED))
    count = f' <tspan fill="{MUTED}">x{e["count"]}</tspan>' if e["count"] > 1 else ""
    p.append(f'<text class="l" xml:space="preserve" x="{PAD}" y="{y}" style="animation-delay:{0.3 + i*0.25:.2f}s">'
             f'<tspan fill="{MUTED}">{ago(e["at"]):>8}</tspan>  '
             f'<tspan fill="{color}" font-weight="bold">{label:<8}</tspan>'
             f'<tspan fill="{ACCENT}">{esc(e["repo"][:repo_w]):<{repo_w}}</tspan>  '
             f'<tspan fill="{INK}">{esc(e["text"][:44])}</tspan>{count}</text>')

y = top + len(events) * LINE
d = 0.3 + len(events) * 0.25
p.append(f'<g class="l" style="animation-delay:{d:.2f}s"><text x="{PAD}" y="{y}" fill="{ACCENT}">~$</text>'
         f'<rect class="c" x="{PAD + 26}" y="{y - 12}" width="8" height="15" fill="{ACCENT}"/></g>')
p.append("</svg>")

with open(OUT, "w") as f:
    f.write("".join(p))
print("wrote", OUT)
