#!/usr/bin/env python3
"""
Render data/contributions.json as an animated contribution heatmap SVG.
Cells pop in along a diagonal sweep (CSS keyframes, plays once), then a
legend and stats footer fade in. GitHub runs the animation inside <img>.
STATIC=1 renders the final frame without animation.
"""
import datetime
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "contrib-heatmap.svg")
STATIC = bool(os.environ.get("STATIC"))

W = 860
CELL, GAP = 12, 3
STEP = CELL + GAP
LEFT, TOP = 46, 62
BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK, ACCENT = "#7d8590", "#c9d1d9", "#8b8cff"
# space-purple palette matching the SpaceEnergy logo, level 0..4
LEVELS = ["#161b22", "#2b2d6e", "#4447b0", "#6a6ef0", "#a3a6ff"]

with open(DATA) as f:
    data = json.load(f)
days = data["days"]

# place each day in a (week, weekday) grid, weeks starting on Sunday
first = datetime.date.fromisoformat(days[0]["date"])
start = first - datetime.timedelta(days=(first.weekday() + 1) % 7)
cells = []
for d in days:
    date = datetime.date.fromisoformat(d["date"])
    idx = (date - start).days
    cells.append((idx // 7, idx % 7, d))
weeks = cells[-1][0] + 1
grid_w = weeks * STEP - GAP
grid_h = 7 * STEP - GAP
H = TOP + grid_h + 74

out = []
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">')
out.append("<style>"
           "@keyframes pop{0%{opacity:0;transform:scale(.2)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:scale(1)}}"
           "@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
           "@keyframes twinkle{0%,100%{opacity:.15}50%{opacity:.9}}"
           ".c{transform-box:fill-box;transform-origin:center}"
           + ("" if STATIC else
              ".c{opacity:0;animation:pop .45s ease-out forwards}"
              ".f{opacity:0;animation:fade .6s ease-out forwards}"
              ".s{animation:twinkle 3s ease-in-out infinite}")
           + "@media (prefers-reduced-motion){.c,.f{animation:none;opacity:1}}"
           "</style>")
out.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>')
out.append(f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>')
out.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>')

# a few twinkling background stars (deterministic positions)
for i in range(18):
    x = (i * 137 + 41) % (W - 20) + 10
    y = (i * 59 + 13) % (H - 20) + 10
    out.append(f'<circle class="s" cx="{x}" cy="{y}" r="{0.6 + (i % 3) * 0.3}" fill="{INK}" '
               f'opacity=".3" style="animation-delay:{(i * 0.37) % 3:.2f}s"/>')

# title bar
out.append(f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="{FRAME}"/>')
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    out.append(f'<circle cx="{20 + i*16}" cy="15" r="5" fill="{c}"/>')
out.append(f'<text x="{W/2}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">'
           f'{data["username"].lower()}@github: ~$ ./contributions.sh</text>')

# month labels
x0 = LEFT + (W - LEFT * 2 - grid_w) / 2
seen = None
for wk, wd, d in cells:
    month = d["date"][:7]
    if wd == 0 and month != seen and wk < weeks - 2:
        seen = month
        name = datetime.date.fromisoformat(d["date"]).strftime("%b")
        out.append(f'<text x="{x0 + wk*STEP}" y="{TOP-8}" fill="{MUTED}" font-size="10">{name}</text>')
for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    out.append(f'<text x="{x0-8}" y="{TOP + wd*STEP + 9}" fill="{MUTED}" font-size="10" text-anchor="end">{name}</text>')

# cells: diagonal sweep, delay grows with week + weekday
for wk, wd, d in cells:
    delay = (wk + wd) * 0.028
    out.append(f'<rect class="c" x="{x0 + wk*STEP}" y="{TOP + wd*STEP}" width="{CELL}" height="{CELL}" rx="2.5" '
               f'fill="{LEVELS[d["level"]]}" style="animation-delay:{delay:.3f}s">'
               f'<title>{d["count"]} on {d["date"]}</title></rect>')

end_delay = (weeks + 6) * 0.028 + 0.3

# legend
ly = TOP + grid_h + 22
lx = x0 + grid_w - 5 * STEP - 70
out.append(f'<g class="f" style="animation-delay:{end_delay:.2f}s">')
out.append(f'<text x="{lx}" y="{ly+10}" fill="{MUTED}" font-size="10">Less</text>')
for i, c in enumerate(LEVELS):
    out.append(f'<rect x="{lx + 32 + i*STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
out.append(f'<text x="{lx + 36 + 5*STEP}" y="{ly+10}" fill="{MUTED}" font-size="10">More</text>')
out.append(f'<text x="{x0}" y="{ly+10}" fill="{MUTED}" font-size="10">'
           f'last updated {data["generated_at"][:10]}</text>')
out.append("</g>")

# stats footer
fy = ly + 38
stats = [
    ("total", f'{data["total_contributions"]:,}'),
    ("active days", str(data["active_days"])),
    ("streak", f'{data["current_streak"]}d'),
    ("longest", f'{data["longest_streak"]}d'),
    ("best day", f'{data["best_day"]["count"]}'),
]
col = grid_w / len(stats)
for i, (k, v) in enumerate(stats):
    out.append(f'<text class="f" xml:space="preserve" x="{x0 + i*col}" y="{fy}" font-size="13" '
               f'style="animation-delay:{end_delay + 0.15*(i+1):.2f}s">'
               f'<tspan fill="{MUTED}">{k}: </tspan><tspan fill="{ACCENT}" font-weight="bold">{v}</tspan></text>')

out.append("</svg>")
with open(OUT, "w") as f:
    f.write("".join(out))
print("wrote", OUT)
