#!/usr/bin/env python3
"""
Render the top repos from data/stats.json as one SVG card per repo
(projects/card-N.svg) and rewrite the README block between the PROJECTS
markers, so every card links to its repo. Cards fade/slide in on a stagger.
STATIC=1 renders the final frame without animation.
"""
import os
import re
import json
import textwrap

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "projects")
README = os.path.join(ROOT, "README.md")
STATIC = bool(os.environ.get("STATIC"))

W, H = 420, 132
PAD = 18
BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK, ACCENT = "#7d8590", "#c9d1d9", "#8b8cff"
GOLD = "#f2c46d"
LANG_COLORS = {
    "CSS": "#663399", "HTML": "#e34c26", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Python": "#3572A5", "Shell": "#89e051", "PowerShell": "#3d7cc9", "Lua": "#5b6ee1",
    "C#": "#178600", "Rust": "#dea584", "Go": "#00ADD8", "Java": "#b07219",
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card(repo, i):
    d0 = i * 0.15
    anim = "" if STATIC else f' class="f" style="animation-delay:{d0:.2f}s"'
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    p.append("<style>@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
             "@keyframes glow{0%,100%{stroke-opacity:.25}50%{stroke-opacity:.8}}"
             ".f{opacity:0;animation:in .6s ease-out forwards}"
             ".g{animation:glow 4s ease-in-out infinite}"
             "@media (prefers-reduced-motion){.f{animation:none;opacity:1}.g{animation:none}}</style>")
    p.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
             f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>')
    p.append(f"<g{anim}>")
    p.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="url(#bg)" stroke="{FRAME}"/>')
    # top-repo gets a softly pulsing accent border
    if i == 0:
        p.append(f'<rect class="g" x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="none" '
                 f'stroke="{ACCENT}" stroke-width="1.5"/>')
    # folder icon
    p.append(f'<path d="M{PAD} 22h7l2 3h9v11h-18z" fill="none" stroke="{ACCENT}" stroke-width="1.4" stroke-linejoin="round"/>')
    p.append(f'<text x="{PAD + 26}" y="34" font-size="14" xml:space="preserve">'
             f'<tspan fill="{MUTED}">{esc(repo["owner"])}/</tspan>'
             f'<tspan fill="{ACCENT}" font-weight="bold">{esc(repo["name"])}</tspan></text>')
    desc = repo["description"] or "no description, just vibes"
    lines = textwrap.wrap(desc, 52)[:2]
    if len(textwrap.wrap(desc, 52)) > 2:
        lines[1] = lines[1][:49].rstrip() + "..."
    for j, line in enumerate(lines):
        p.append(f'<text x="{PAD}" y="{60 + j*18}" fill="{INK}" font-size="12">{esc(line)}</text>')
    # footer: language, stars, forks, my commits
    fy = H - 18
    x = PAD
    if repo["language"]:
        p.append(f'<circle cx="{x + 5}" cy="{fy - 4}" r="5" fill="{LANG_COLORS.get(repo["language"], ACCENT)}"/>')
        p.append(f'<text x="{x + 15}" y="{fy}" fill="{MUTED}" font-size="12">{esc(repo["language"])}</text>')
        x += 24 + len(repo["language"]) * 7.3
    p.append(f'<path transform="translate({x} {fy - 11}) scale(.75)" fill="{GOLD}" '
             f'd="M8 .25l2.4 4.9 5.4.8-3.9 3.8.9 5.4L8 12.6l-4.8 2.5.9-5.4L.2 5.9l5.4-.8z"/>')
    p.append(f'<text x="{x + 16}" y="{fy}" fill="{MUTED}" font-size="12">{repo["stars"]}</text>')
    x += 28 + len(str(repo["stars"])) * 7.3
    p.append(f'<path transform="translate({x} {fy - 11}) scale(.75)" fill="none" stroke="{MUTED}" stroke-width="1.6" '
             f'd="M4 3v3a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V3M8 8v5"/>'
             f'<circle cx="{x + 3}" cy="{fy - 9.5}" r="1.6" fill="{MUTED}"/><circle cx="{x + 9}" cy="{fy - 9.5}" r="1.6" fill="{MUTED}"/>'
             f'<circle cx="{x + 6}" cy="{fy - 1.5}" r="1.6" fill="{MUTED}"/>')
    p.append(f'<text x="{x + 16}" y="{fy}" fill="{MUTED}" font-size="12">{repo["forks"]}</text>')
    p.append(f'<text x="{W - PAD}" y="{fy}" font-size="12" text-anchor="end" xml:space="preserve">'
             f'<tspan fill="{ACCENT}" font-weight="bold">{repo["commits"]:,}</tspan>'
             f'<tspan fill="{MUTED}"> commits by me</tspan></text>')
    p.append("</g></svg>")
    return "".join(p)


with open(os.path.join(ROOT, "data", "stats.json")) as f:
    repos = json.load(f).get("top_repos", [])

os.makedirs(OUT_DIR, exist_ok=True)
for old in os.listdir(OUT_DIR):
    if old.startswith("card-") and old.endswith(".svg"):
        os.remove(os.path.join(OUT_DIR, old))
cells = []
for i, repo in enumerate(repos):
    path = f"projects/card-{i}.svg"
    with open(os.path.join(ROOT, path), "w") as f:
        f.write(card(repo, i))
    url = f'https://github.com/{repo["owner"]}/{repo["name"]}'
    cells.append(f'<td><a href="{url}"><img src="./{path}" width="415" alt="{repo["owner"]}/{repo["name"]}" /></a></td>')

rows = "\n".join("<tr>\n" + "\n".join(cells[i:i + 2]) + "\n</tr>" for i in range(0, len(cells), 2))
block = f"<!--PROJECTS:START-->\n<table>\n{rows}\n</table>\n<!--PROJECTS:END-->"
with open(README) as f:
    readme = f.read()
readme, n = re.subn(r"<!--PROJECTS:START-->.*?<!--PROJECTS:END-->", lambda _: block, readme, flags=re.S)
if n:
    with open(README, "w") as f:
        f.write(readme)
print(f"wrote {len(repos)} project cards" + (", updated README" if n else " (no PROJECTS markers in README)"))
