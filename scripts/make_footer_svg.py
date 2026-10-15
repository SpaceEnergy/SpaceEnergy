#!/usr/bin/env python3
"""
One-time: an animated space scene for the bottom of the README - twinkling
stars, a ringed planet with an orbiting moon, a rocket crossing the sky and
the odd shooting star. STATIC=1 renders a still frame.
"""
import os
import random

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "footer.svg")
STATIC = bool(os.environ.get("STATIC"))

W, H = 860, 220
BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK, ACCENT = "#7d8590", "#c9d1d9", "#8b8cff"
rnd = random.Random(7)

p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
     f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
p.append("<style>"
         "@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}"
         "@keyframes fly{0%{transform:translate(330px,250px) rotate(-28deg)}100%{transform:translate(920px,-40px) rotate(-28deg)}}"
         "@keyframes flame{0%,100%{transform:scaleX(1)}50%{transform:scaleX(.6)}}"
         "@keyframes shoot{0%,88%{opacity:0;transform:translate(0,0)}90%{opacity:1}100%{opacity:0;transform:translate(-260px,130px)}}"
         "@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}"
         + ("" if STATIC else
            ".s{animation:tw 3s ease-in-out infinite}"
            ".rocket{animation:fly 9s linear infinite}"
            ".flame{transform-box:fill-box;transform-origin:100% 50%;animation:flame .15s ease-in-out infinite}"
            ".shoot{animation:shoot 7s ease-in infinite}"
            ".planet{animation:float 6s ease-in-out infinite}")
         + "@media (prefers-reduced-motion){.s,.rocket,.flame,.shoot,.planet{animation:none}}"
         "</style>")
p.append("<defs>"
         f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG}"/>'
         f'<stop offset="1" stop-color="#161233"/></linearGradient>'
         '<radialGradient id="pl" cx=".35" cy=".35" r=".75"><stop offset="0" stop-color="#a3a6ff"/>'
         '<stop offset=".55" stop-color="#4447b0"/><stop offset="1" stop-color="#1b1d4d"/></radialGradient>'
         '<radialGradient id="glow" r=".5"><stop offset="0" stop-color="#8b8cff" stop-opacity=".35"/>'
         '<stop offset="1" stop-color="#8b8cff" stop-opacity="0"/></radialGradient>'
         '<linearGradient id="tail" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
         '<stop offset="1" stop-color="#fff"/></linearGradient>'
         "</defs>")
p.append(f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>')
p.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>')

# stars
for _ in range(70):
    x, y = rnd.uniform(10, W - 10), rnd.uniform(10, H - 10)
    r = rnd.choice([0.6, 0.8, 1, 1.3])
    p.append(f'<circle class="s" cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" opacity=".6" '
             f'style="animation-delay:{rnd.uniform(0, 3):.2f}s;animation-duration:{rnd.uniform(2, 5):.1f}s"/>')

# shooting star
p.append('<g class="shoot"><line x1="720" y1="30" x2="780" y2="0" stroke="url(#tail)" stroke-width="1.5" '
         'transform="rotate(180 750 15)"/></g>')

# planet with ring (back half of ring, planet, front half) and an orbiting moon
cx, cy, r = 690, 110, 46
p.append('<g class="planet">')
p.append(f'<circle cx="{cx}" cy="{cy}" r="{r * 2.2}" fill="url(#glow)"/>')
ring = f'cx="{cx}" cy="{cy}" rx="{r * 1.75}" ry="{r * 0.42}" transform="rotate(-18 {cx} {cy})"'
p.append(f'<ellipse {ring} fill="none" stroke="#6a6ef0" stroke-width="5" stroke-opacity=".5"/>')
p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#pl)"/>')
p.append(f'<path d="M{cx - r * 0.7} {cy - r * 0.2}q{r * 0.7} {-r * 0.25} {r * 1.4} {r * 0.05}" fill="none" '
         f'stroke="#c9caff" stroke-opacity=".25" stroke-width="4" stroke-linecap="round"/>')
# front half of the ring drawn over the planet
p.append(f'<clipPath id="front"><rect x="{cx - r * 2}" y="{cy}" width="{r * 4}" height="{r}" transform="rotate(-18 {cx} {cy})"/></clipPath>')
p.append(f'<ellipse {ring} fill="none" stroke="#a3a6ff" stroke-width="5" stroke-opacity=".75" clip-path="url(#front)"/>')
orbit = f"M{cx - 115},{cy} a115,38 0 1,0 230,0 a115,38 0 1,0 -230,0"
p.append(f'<circle r="7" fill="#c9d1d9"><animateMotion dur="{"0" if STATIC else "12"}s" repeatCount="indefinite" '
         f'path="{orbit}"/></circle>' if not STATIC else f'<circle cx="{cx - 110}" cy="{cy + 12}" r="7" fill="#c9d1d9"/>')
p.append("</g>")

# rocket (drawn pointing right, flies diagonally up)
p.append('<g class="rocket"><g transform="scale(.9)">'
         '<path class="flame" d="M-2 0 L-26 -6 L-18 0 L-26 6 Z" fill="#ff8f6b"/>'
         '<path class="flame" d="M-2 0 L-16 -3 L-11 0 L-16 3 Z" fill="#f2c46d"/>'
         '<path d="M0 -8 H30 Q44 -8 50 0 Q44 8 30 8 H0 Z" fill="#c9d1d9"/>'
         '<path d="M4 -8 L-6 -18 L14 -8 Z M4 8 L-6 18 L14 8 Z" fill="#8b8cff"/>'
         '<circle cx="30" cy="0" r="4.5" fill="#4447b0" stroke="#0d1117" stroke-width="1.5"/>'
         "</g></g>"
         if not STATIC else
         '<g transform="translate(500 160) rotate(-28) scale(.9)">'
         '<path d="M-2 0 L-26 -6 L-18 0 L-26 6 Z" fill="#ff8f6b"/>'
         '<path d="M0 -8 H30 Q44 -8 50 0 Q44 8 30 8 H0 Z" fill="#c9d1d9"/>'
         '<path d="M4 -8 L-6 -18 L14 -8 Z M4 8 L-6 18 L14 8 Z" fill="#8b8cff"/>'
         '<circle cx="30" cy="0" r="4.5" fill="#4447b0" stroke="#0d1117" stroke-width="1.5"/></g>')

# sign-off
p.append(f'<text x="40" y="100" fill="{INK}" font-size="20" font-weight="bold">thanks for stopping by</text>')
p.append(f'<text x="40" y="128" fill="{MUTED}" font-size="14">see you among the stars</text>')
p.append(f'<text x="40" y="180" fill="{MUTED}" font-size="13" xml:space="preserve">'
         f'<tspan fill="{ACCENT}">~$</tspan> exit</text>')
p.append(f'<rect x="96" y="169" width="8" height="14" fill="{ACCENT}">'
         '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.51;1" dur="1s" repeatCount="indefinite"/></rect>')
p.append("</svg>")

with open(OUT, "w") as f:
    f.write("".join(p))
print("wrote", OUT)
