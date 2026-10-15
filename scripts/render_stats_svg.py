#!/usr/bin/env python3
"""
Render data/stats.json (+ streaks from data/contributions.json) as an animated
terminal-style stats card: overview tiles, a 24h commit clock, weekday bars and
a language breakdown. Bars grow in once via CSS keyframes, then hold.
STATIC=1 renders the final frame without animation.
"""
import datetime
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "stats.svg")
STATIC = bool(os.environ.get("STATIC"))

with open(os.path.join(ROOT, "data", "stats.json")) as f:
    data = json.load(f)
with open(os.path.join(ROOT, "data", "contributions.json")) as f:
    contrib = json.load(f)

W = 860
PAD = 20
GAP = 12
BG, BG2, FRAME, PANEL = "#0d1117", "#111722", "#30363d", "#161b22"
MUTED, INK, ACCENT, KEY = "#7d8590", "#c9d1d9", "#8b8cff", "#a3a6ff"
TRACK = "#21262d"
PERIODS = [  # (name, hours, color, verdict)
    ("night", range(0, 6), "#6a6ef0", "Night Owl"),
    ("morning", range(6, 12), "#f2c46d", "Early Bird"),
    ("daytime", range(12, 18), "#7ee0b5", "Daytime Grinder"),
    ("evening", range(18, 24), "#ff8f6b", "Twilight Taskmaster"),
]
LANG_COLORS = {
    "CSS": "#663399", "HTML": "#e34c26", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Python": "#3572A5", "Shell": "#89e051", "PowerShell": "#3d7cc9", "Markdown": "#083fa1",
    "Java": "#b07219", "C#": "#178600", "C++": "#f34b7d", "C": "#555555", "Go": "#00ADD8",
    "Rust": "#dea584", "Lua": "#5b6ee1", "SCSS": "#c6538c", "Vue": "#41b883", "PHP": "#4F5D95",
    "Batchfile": "#C1F12E", "Dockerfile": "#384d54", "Kotlin": "#A97BFF", "Svelte": "#ff3e00",
}
FALLBACK = ["#8b8cff", "#a3a6ff", "#6a6ef0", "#4447b0"]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt(n):
    return f"{n:,}".replace(",", ".")


out = []
add = out.append
delay = 0.0  # running animation clock


def text(x, y, s, fill=INK, size=12, anchor="start", weight=None, cls="f", d=None, preserve=False):
    attrs = f'x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}"'
    if anchor != "start":
        attrs += f' text-anchor="{anchor}"'
    if weight:
        attrs += f' font-weight="{weight}"'
    if preserve:
        attrs += ' xml:space="preserve"'
    if cls:
        attrs += f' class="{cls}" style="animation-delay:{(delay if d is None else d):.2f}s"'
    add(f"<text {attrs}>{s}</text>")


def panel(x, y, w, h, title, sub=""):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{PANEL}" stroke="{FRAME}"/>')
    text(x + 16, y + 26, f'<tspan fill="{MUTED}">// </tspan>{esc(title)}', fill=INK, size=13, weight="bold", preserve=True)
    if sub:
        text(x + w - 16, y + 26, sub, fill=ACCENT, size=12, anchor="end", weight="bold")


# ---- layout -----------------------------------------------------------------
TB = 30
tiles_y = TB + 20
tiles_h = 66
row_y = tiles_y + tiles_h + GAP
row_h = 250
lang_y = row_y + row_h + GAP
lang_rows = max(1, -(-min(len(data["languages"]), 9) // 4))  # legend rows, 4 per row
lang_h = 74 + lang_rows * 22
H = lang_y + lang_h + 40

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">')
add("<style>"
    "@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}"
    "@keyframes gy{from{transform:scaleY(0)}to{transform:scaleY(1)}}"
    "@keyframes gx{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    ".vb,.hb{transform-box:fill-box}.vb{transform-origin:50% 100%}.hb{transform-origin:0 50%}"
    + ("" if STATIC else
       ".f{opacity:0;animation:fade .5s ease-out forwards}"
       ".vb{transform:scaleY(0);animation:gy .6s cubic-bezier(.2,.8,.2,1) forwards}"
       ".hb{transform:scaleX(0);animation:gx .7s cubic-bezier(.2,.8,.2,1) forwards}")
    + "@media (prefers-reduced-motion){.f,.vb,.hb{animation:none;opacity:1;transform:none}}"
    "</style>")
add(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>')
add(f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>')
add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>')
add(f'<line x1="0" y1="{TB}" x2="{W}" y2="{TB}" stroke="{FRAME}"/>')
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    add(f'<circle cx="{20 + i*16}" cy="15" r="5" fill="{c}"/>')
text(W / 2, 19, f'{data["username"].lower()}@github: ~$ ./stats.sh', fill=MUTED, size=12, anchor="middle", cls=None)

# ---- overview tiles -----------------------------------------------------------
tiles = [
    ("commits", fmt(data["total_commits"])),
    ("streak", f'{contrib["current_streak"]}d'),
    ("longest", f'{contrib["longest_streak"]}d'),
    ("repos", fmt(data["repos"])),
    ("orgs", str(len(data.get("orgs", [])))),
    ("stars", fmt(data["stars"])),
]
tw = (W - 2 * PAD - (len(tiles) - 1) * GAP) / len(tiles)
for i, (label, value) in enumerate(tiles):
    x = PAD + i * (tw + GAP)
    delay = 0.1 + i * 0.08
    add(f'<g class="f" style="animation-delay:{delay:.2f}s">'
        f'<rect x="{x:.1f}" y="{tiles_y}" width="{tw:.1f}" height="{tiles_h}" rx="8" fill="{PANEL}" stroke="{FRAME}"/></g>')
    text(x + tw / 2, tiles_y + 36, value, fill=ACCENT, size=22, anchor="middle", weight="bold")
    text(x + tw / 2, tiles_y + 54, label, fill=MUTED, size=11, anchor="middle")

# ---- commit clock (24h) -------------------------------------------------------
hours = data["hours"]
total_h = sum(hours) or 1
period_sums = [sum(hours[h] for h in rng) for _, rng, _, _ in PERIODS]
best_period = PERIODS[period_sums.index(max(period_sums))]
pw = (W - 2 * PAD - GAP) / 2
px0 = PAD
delay = 0.6
panel(px0, row_y, pw, row_h, "when I code", f"I'm a {best_period[3]}")

chart_x = px0 + 16
chart_w = pw - 32
chart_top = row_y + 50
chart_h = 110
step = chart_w / 24
mx = max(hours) or 1
color_of = {h: c for _, rng, c, _ in PERIODS for h in rng}
base = chart_top + chart_h
add(f'<line x1="{chart_x}" y1="{base}" x2="{chart_x + chart_w}" y2="{base}" stroke="{FRAME}"/>')
for h, n in enumerate(hours):
    bh = max(2, n / mx * chart_h)
    add(f'<rect class="vb" x="{chart_x + h*step + 2:.1f}" y="{base - bh:.1f}" width="{step - 4:.1f}" '
        f'height="{bh:.1f}" rx="2" fill="{color_of[h]}" style="animation-delay:{delay + h*0.035:.2f}s"/>')
for h in (0, 6, 12, 18):
    text(chart_x + h * step + step / 2, base + 16, f"{h:02d}", fill=MUTED, size=10, anchor="middle", cls=None)
text(chart_x + chart_w - step / 2, base + 16, "23", fill=MUTED, size=10, anchor="middle", cls=None)

# period legend: 2x2
delay += 24 * 0.035 + 0.2
ly = base + 40
for i, ((name, _, color, _), n) in enumerate(zip(PERIODS, period_sums)):
    cx = chart_x + (i % 2) * (chart_w / 2)
    cy = ly + (i // 2) * 24
    d = delay + i * 0.08
    add(f'<rect class="f" x="{cx:.1f}" y="{cy - 9}" width="10" height="10" rx="2" fill="{color}" '
        f'style="animation-delay:{d:.2f}s"/>')
    text(cx + 18, cy, f'{name:<8}<tspan fill="{ACCENT}" font-weight="bold">{n / total_h * 100:5.1f}%</tspan>'
         f'<tspan fill="{MUTED}"> {fmt(n)}</tspan>', size=12, d=d, preserve=True)

# ---- weekdays -------------------------------------------------------------------
days = data["weekdays"]  # Monday first
names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
total_d = sum(days) or 1
best = days.index(max(days))
long_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
qx = PAD + pw + GAP
delay = 0.8
panel(qx, row_y, pw, row_h, "most productive", long_names[best])
bar_x = qx + 60
bar_w = pw - 60 - 110
mxd = max(days) or 1
for i, n in enumerate(days):
    y = row_y + 50 + i * 26
    d = delay + i * 0.09
    fill = ACCENT if i == best else "#4447b0"
    text(qx + 16, y + 11, names[i], fill=INK if i == best else MUTED, size=12, d=d,
         weight="bold" if i == best else None)
    add(f'<rect x="{bar_x}" y="{y}" width="{bar_w:.1f}" height="14" rx="3" fill="{TRACK}"/>')
    add(f'<rect class="hb" x="{bar_x}" y="{y}" width="{max(3, n / mxd * bar_w):.1f}" height="14" rx="3" '
        f'fill="{fill}" style="animation-delay:{d:.2f}s"/>')
    text(qx + pw - 16, y + 11, f'<tspan fill="{ACCENT if i == best else INK}" font-weight="bold">'
         f'{n / total_d * 100:.1f}%</tspan><tspan fill="{MUTED}"> {fmt(n):>5}</tspan>',
         size=12, anchor="end", d=d + 0.3, preserve=True)

# ---- languages ------------------------------------------------------------------
langs = data["languages"]
total_b = sum(l["bytes"] for l in langs) or 1
# top 8 that round to at least 0.1%, everything else becomes "Other"
top = [l for l in langs[:8] if l["bytes"] / total_b >= 0.0005]
rest = total_b - sum(l["bytes"] for l in top)
if rest / total_b >= 0.0005:
    top.append({"name": "Other", "bytes": rest, "repos": 0})
colors = {}
for i, l in enumerate(top):
    colors[l["name"]] = LANG_COLORS.get(l["name"], "#484f58" if l["name"] == "Other" else FALLBACK[i % 4])

delay = 1.6
panel(PAD, lang_y, W - 2 * PAD, lang_h, "languages", f'mostly {top[0]["name"]}' if top else "")
sx, sw, sy = PAD + 16, W - 2 * PAD - 32, lang_y + 42
add(f'<clipPath id="lc"><rect x="{sx}" y="{sy}" width="{sw}" height="12" rx="6"/></clipPath>')
add(f'<rect x="{sx}" y="{sy}" width="{sw}" height="12" rx="6" fill="{TRACK}"/>')
add('<g clip-path="url(#lc)">')
cx = sx
for i, l in enumerate(top):
    seg = l["bytes"] / total_b * sw
    # 1px overlap hides antialiasing seams between segments
    add(f'<rect class="hb" x="{cx:.1f}" y="{sy}" width="{seg + 1:.1f}" height="12" fill="{colors[l["name"]]}" '
        f'style="animation-delay:{delay + i*0.12:.2f}s"/>')
    cx += seg
add("</g>")
delay += len(top) * 0.12
cols = 4
cw = sw / cols
for i, l in enumerate(top):
    lx = sx + (i % cols) * cw
    ly = sy + 40 + (i // cols) * 22
    d = delay + i * 0.06
    add(f'<circle class="f" cx="{lx + 5:.1f}" cy="{ly - 4}" r="5" fill="{colors[l["name"]]}" '
        f'style="animation-delay:{d:.2f}s"/>')
    text(lx + 16, ly, f'{esc(l["name"])} <tspan fill="{MUTED}">{l["bytes"] / total_b * 100:.1f}%</tspan>',
         size=12, d=d, preserve=True)

# ---- footer ---------------------------------------------------------------------
updated = datetime.datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00")).strftime("%Y-%m-%d")
text(PAD, H - 16, f'<tspan fill="{ACCENT}">~$</tspan> last updated {updated} · times in {data["time_zone"]}'
     + (f' · incl. {esc(", ".join(data["orgs"]))}' if data.get("orgs") else ""),
     fill=MUTED, size=11, d=delay + 0.6, preserve=True)

add("</svg>")
with open(OUT, "w") as f:
    f.write("".join(out))
print("wrote", OUT)
