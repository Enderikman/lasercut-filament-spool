#!/usr/bin/env python3
"""Laser-cut spool for Bambu Lab refills. Output: spule.svg (mm units).
Edit the parameters, rerun: python3 gen_spule.py"""
import math, os

T = 3.0        # material thickness
KERF = 0.15    # laser kerf; raise for tighter press fit
OD = float(os.environ.get("SPULE_OD", 200.0))  # flange outer diameter (AMS: 197-202); gen_doppel.py overrides it
BORE = 55.0    # centre bore
HUB = 80.5     # hub diameter over rib edges (refill core ID ~82, measure!)
INNER_W = 60.0 # clear width between flanges (refill ~59-60)
N_RIBS = 6
N_PLAIN = 3      # plain ribs cut here; the other N_RIBS - N_PLAIN are lockable ribs from gen_riegel.py
TAB = 7.0      # tab width (radial)
GAP = 5.0
# fill gauge: window + gram scale (approx, m ~ r^2 - r0^2)
R_EMPTY = 43.0   # winding start radius (core outer), measure!
FULL_G = 1000
DENSITY = 1.24   # g/cm3: PLA 1.24, PETG 1.27, ABS 1.05, TPU 1.21
PACK = 0.85      # winding fill factor (air between strands), estimate
R_FULL_MEASURED = None  # outer radius of the full winding in mm; set this to override the estimate
# 97.5 (flange edge) was wrong: a 1 kg winding only reaches ~83 mm, so the old scale read ~30 % low
R_FULL = R_FULL_MEASURED or math.sqrt(R_EMPTY**2 + FULL_G / DENSITY / PACK * 1000 / (math.pi * INNER_W))
WIN_R0, WIN_R1, WIN_W = 45.0, OD / 2 - 4, 8.0
R_HOLE = OD / 2 - 4.5   # filament end holes, just inside the rim

r_in, r_out = BORE / 2, HUB / 2
rib_h = r_out - r_in
tab_off = (rib_h - TAB) / 2
r_tab = r_in + tab_off          # radial start of tab
S = 'fill="none" stroke="#ff0000" stroke-width="0.1"'
E = 'fill="none" stroke="#0000ff" stroke-width="0.1"'   # score/engrave layer
SEG = {"a": (0, 0, 1, 0), "b": (1, 0, 1, .5), "c": (1, .5, 1, 1), "d": (0, 1, 1, 1),
       "e": (0, .5, 0, 1), "f": (0, 0, 0, .5), "g": (0, .5, 1, .5)}
DIG = {"0": "abcdef", "1": "bc", "2": "abged", "5": "afgcd", "7": "abc"}

def r_for(g):
    return math.sqrt(R_EMPTY**2 + g / FULL_G * (R_FULL**2 - R_EMPTY**2))

def text(x, y, txt, h=4.0, w=2.2, sp=1.0):
    for ch in txt:
        for k in DIG[ch]:
            x1, y1, x2, y2 = SEG[k]
            out.append(f'<line x1="{x+x1*w:.3f}" y1="{y+y1*h:.3f}" x2="{x+x2*w:.3f}" y2="{y+y2*h:.3f}" {E}/>')
        x += w + sp

def gauge(cx, cy):
    hw = WIN_W / 2
    out.append(f'<rect x="{cx-hw}" y="{cy-WIN_R1}" width="{WIN_W}" height="{WIN_R1-WIN_R0}" rx="{hw}" {S}/>')
    for g in range(100, FULL_G, 100):
        r = r_for(g)
        if not WIN_R0 + hw < r < WIN_R1 - 1:
            continue
        major = g in (250, 500, 750) or g % 250 == 0
        out.append(f'<line x1="{cx+hw+1}" y1="{cy-r:.3f}" x2="{cx+hw+(5 if major else 3)}" y2="{cy-r:.3f}" {E}/>')
    for g in (250, 500, 750):
        r = r_for(g)
        out.append(f'<line x1="{cx+hw+1}" y1="{cy-r:.3f}" x2="{cx+hw+5}" y2="{cy-r:.3f}" {E}/>')
        text(cx + hw + 6.5, cy - r - 2, str(g))
out = []

def flange(cx, cy, with_gauge=False):
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{OD/2}" {S}/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r_in}" {S}/>')
    sl, sw = TAB - KERF, T - KERF
    for i in range(N_RIBS):
        a = 360 / N_RIBS * i
        out.append(f'<rect x="{cx + r_tab + KERF/2:.3f}" y="{cy - sw/2:.3f}" width="{sl:.3f}" '
                   f'height="{sw:.3f}" transform="rotate({a} {cx} {cy})" {S}/>')
    for i in range(3):  # filament end holes
        a = math.radians(90 + 120 * i)
        out.append(f'<circle cx="{cx + R_HOLE*math.cos(a):.3f}" cy="{cy + R_HOLE*math.sin(a):.3f}" r="1.5" {S}/>')
    if with_gauge:
        gauge(cx, cy)

def rib(x, y):  # vertical: length along y
    L = INNER_W + 2 * T
    a, b = tab_off - KERF/2, tab_off + TAB + KERF/2
    pts = [(0, T), (a, T), (a, 0), (b, 0), (b, T), (rib_h, T), (rib_h, L - T),
           (b, L - T), (b, L), (a, L), (a, L - T), (0, L - T)]
    d = "M" + " L".join(f"{x+px:.3f},{y+py:.3f}" for px, py in pts) + " Z"
    out.append(f'<path d="{d}" {S}/>')

if __name__ == "__main__":
    # staggered layout so both flanges fit a sheet narrower than 2x OD
    SHEET_W = 391.0  # usable material width
    PART_GAP = 2.0
    dx = SHEET_W - OD
    dy = math.ceil(math.sqrt(max((OD + PART_GAP)**2 - dx**2, 0)))
    flange(OD/2, OD/2, with_gauge=True)
    flange(OD/2 + dx, OD/2 + dy)
    rib_y = OD + 4
    for i in range(N_PLAIN):
        rib(i * (rib_h + PART_GAP), rib_y)
    W = SHEET_W
    H = max(OD + dy, rib_y + INNER_W + 2*T)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" '
           f'viewBox="0 0 {W} {H}">\n' + "\n".join(out) + "\n</svg>\n")
    open("spule.svg", "w").write(svg)
    print(f"spule.svg {W} x {H} mm, rib {rib_h} x {INNER_W + 2*T}, total width {INNER_W + 2*T}")
