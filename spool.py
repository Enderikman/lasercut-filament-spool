#!/usr/bin/env python3
"""Laser-cut filament spool, compatible with Bambu Lab filament refills. No glue needed.

Run:  python3 spool.py        -> writes spool.svg (units: mm)

One sheet holds a complete spool: 2 flanges, 6 ribs, 12 snap-on clips.
Red = cut, blue = light score (fill-level scale). No dependencies."""
import math

# --- things you may want to change ---------------------------------------------------------
T = 3.0            # sheet thickness (measure yours)
KERF = 0.15        # laser kerf for slots and tabs; raise for a tighter fit, lower for looser
OD = 174.0         # flange diameter. 174 is what I use; 197-202 is the usual full-size spool
BORE = 55.0        # centre hole
HUB = 80.5         # hub diameter over the rib edges (inside of the refill's cardboard core)
INNER_W = 60.0     # clear width between the flanges (width of the refill)

# fill gauge: window in one flange plus a gram scale
R_EMPTY = 43.0     # radius where the winding starts
FULL_G = 1000      # grams on a full refill
DENSITY = 1.24     # g/cm3: PLA 1.24, PETG 1.27, ABS 1.05, TPU 1.21
PACK = 0.85        # how densely the filament is wound (estimate)
R_FULL_MEASURED = None   # measured outer radius of a full winding in mm; overrides the estimate

# clips: they snap onto the rib necks outside the flange
CLIP_KERF = 0.2
THROAT = 2.3       # opening the neck has to snap through; smaller = harder to push on
SEAT = 3.5         # where the neck rests; smaller than the 4 mm neck, so it clamps
LEG = 3.4          # leg width; thinner = easier to snap on but weaker
CLIP_L = 36.0      # clip length; longer = more flex
# -------------------------------------------------------------------------------------------

N_RIBS = 6
TAB = 7.0          # tab width, matches the flange slots
NECK = 4.0         # rib neck the clip grabs
THROUGH = T + 0.15           # tab length inside the flange
NOTCH = T + 0.3 - KERF       # neck length
HEAD = 2.5                   # rib head outside the clip
GAP = 2.0                    # spacing between parts on the sheet
CLEAR = 1.5                  # minimum distance between cuts

CUT = 'fill="none" stroke="#ff0000" stroke-width="0.1"'
SCORE = 'fill="none" stroke="#0000ff" stroke-width="0.1"'
out = []

R_FULL = R_FULL_MEASURED or math.sqrt(R_EMPTY**2 + FULL_G / DENSITY / PACK * 1000 / (math.pi * INNER_W))
WIN_R0, WIN_R1, WIN_W = 45.0, OD / 2 - 4, 8.0
R_HOLE = OD / 2 - 4.5        # small holes to park the filament end
rib_h = (HUB - BORE) / 2
r_tab = BORE / 2 + (rib_h - TAB) / 2


def path(pts, x=0.0, y=0.0):
    out.append('<path d="M' + " L".join(f"{x+px:.3f},{y+py:.3f}" for px, py in pts) + f' Z" {CUT}/>')


def line(x1, y1, x2, y2):
    out.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" {SCORE}/>')


# --- flange --------------------------------------------------------------------------------
SEG = {"a": (0, 0, 1, 0), "b": (1, 0, 1, .5), "c": (1, .5, 1, 1), "d": (0, 1, 1, 1),
       "e": (0, .5, 0, 1), "f": (0, 0, 0, .5), "g": (0, .5, 1, .5)}
DIGITS = {"0": "abcdef", "1": "bc", "2": "abged", "5": "afgcd", "7": "abc"}


def number(x, y, txt, h=4.0, w=2.2, sp=1.0):
    for ch in txt:
        for k in DIGITS[ch]:
            x1, y1, x2, y2 = SEG[k]
            line(x + x1 * w, y + y1 * h, x + x2 * w, y + y2 * h)
        x += w + sp


def radius_for(grams):
    return math.sqrt(R_EMPTY**2 + grams / FULL_G * (R_FULL**2 - R_EMPTY**2))


def gauge(cx, cy):
    hw = WIN_W / 2
    out.append(f'<rect x="{cx-hw}" y="{cy-WIN_R1}" width="{WIN_W}" height="{WIN_R1-WIN_R0}" rx="{hw}" {CUT}/>')
    for g in range(100, FULL_G, 100):
        r = radius_for(g)
        if WIN_R0 + hw < r < WIN_R1 - 1:
            line(cx + hw + 1, cy - r, cx + hw + (5 if g % 250 == 0 else 3), cy - r)
    for g in (250, 500, 750):
        r = radius_for(g)
        line(cx + hw + 1, cy - r, cx + hw + 5, cy - r)
        number(cx + hw + 6.5, cy - r - 2, str(g))


def flange(cx, cy, with_gauge=False):
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{OD/2}" {CUT}/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{BORE/2}" {CUT}/>')
    sl, sw = TAB - KERF, T - KERF
    for i in range(N_RIBS):
        out.append(f'<rect x="{cx + r_tab + KERF/2:.3f}" y="{cy - sw/2:.3f}" width="{sl:.3f}" height="{sw:.3f}" '
                   f'transform="rotate({360 / N_RIBS * i} {cx} {cy})" {CUT}/>')
    for i in range(3):
        a = math.radians(90 + 120 * i)
        out.append(f'<circle cx="{cx + R_HOLE*math.cos(a):.3f}" cy="{cy + R_HOLE*math.sin(a):.3f}" r="1.5" {CUT}/>')
    if with_gauge:
        gauge(cx, cy)


# --- rib (drawn lying down: length along x) -------------------------------------------------
RIB_END = THROUGH + NOTCH + HEAD
RIB_L, RIB_W = INNER_W + 2 * RIB_END, rib_h


def rib(x, y):
    c = rib_h / 2
    a, b = c - (TAB + KERF) / 2, c + (TAB + KERF) / 2
    n1, n2 = c - (NECK + KERF) / 2, c + (NECK + KERF) / 2
    y1, y2 = RIB_END - THROUGH, RIB_END - THROUGH - NOTCH
    top = [(0, RIB_END), (a, RIB_END), (a, y1), (n1, y1), (n1, y2), (a, y2), (a, 0.5), (a + 0.5, 0),
           (b - 0.5, 0), (b, 0.5), (b, y2), (n2, y2), (n2, y1), (b, y1), (b, RIB_END), (rib_h, RIB_END)]
    pts = top + [(px, RIB_L - py) for px, py in reversed(top)]
    path([(py, px) for px, py in pts], x, y)


# --- clip ----------------------------------------------------------------------------------
_k = CLIP_KERF / 2
_t, _s, _m, _slit = THROAT / 2 - _k, SEAT / 2 - _k, SEAT / 2 + 0.5, 0.5 - _k
_jaw, _leg = SEAT / 2 + LEG, 0.5 + LEG
RAMP, LAND = 2.5, 2.1                       # entry ramp, length of the hook behind the neck
_hook = RAMP + LAND
_seat = _hook + T + 0.1
CLIP_W = 2 * _jaw


def clip(x, y):
    inner = [(0, _m), (RAMP, _t), (_hook, _t), (_hook, _s), (_seat, _s), (_seat + 0.4, _slit), (CLIP_L - 4, _slit)]
    outer = [(CLIP_L, _jaw), (CLIP_L - 2.5, _jaw), (CLIP_L - 3.5, _leg), (_seat + 1.5, _leg), (_seat + 0.5, _jaw), (0, _jaw)]
    pts = ([(px, -py) for px, py in inner] + list(reversed(inner)) +
           list(reversed(outer)) + [(px, -py) for px, py in outer])
    path(pts, x, y + CLIP_W / 2)


# --- layout: both flanges side by side, small parts in the gaps and underneath ---------------
C = [(OD / 2, OD / 2), (OD / 2 + OD + GAP, OD / 2)]
SHEET_W = 2 * OD + GAP
placed = []                                 # (x1, y1, x2, y2, bore centre or None)


def put(draw, x, y, w, h, bore=None):
    draw(x, y)
    placed.append((x, y, x + w, y + h, bore))


flange(*C[0], with_gauge=True)
flange(*C[1])
block = 3 * CLIP_W + 2 * GAP
for c in C:                                 # 3 clips inside each centre hole (waste anyway)
    for i in range(3):
        put(clip, c[0] - CLIP_L / 2, c[1] - block / 2 + i * (CLIP_W + GAP), CLIP_L, CLIP_W, bore=c)
mid = SHEET_W / 2 - CLIP_L / 2
for i in range(2):                          # 2 + 2 clips in the gaps between the flanges
    put(clip, mid, i * (CLIP_W + GAP), CLIP_L, CLIP_W)
    put(clip, mid, OD - CLIP_W - i * (CLIP_W + GAP), CLIP_L, CLIP_W)
row = OD + GAP
for i in range(4):                          # ribs underneath
    put(rib, i * (RIB_L + GAP), row, RIB_L, RIB_W)
for i in range(2):
    put(rib, i * (RIB_L + GAP), row + RIB_W + GAP, RIB_L, RIB_W)
for i in range(2):                          # last 2 clips next to the ribs
    put(clip, 2 * (RIB_L + GAP) + i * (CLIP_L + GAP), row + RIB_W + GAP, CLIP_L, CLIP_W)
SHEET_H = max(p[3] for p in placed)

# safety checks, so a changed parameter cannot silently produce overlapping cuts
for x1, y1, x2, y2, bore in placed:
    corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
    if bore:
        assert max(math.dist(p, bore) for p in corners) <= BORE / 2 - 1.0, "clips do not fit in the centre hole"
        continue
    assert x1 >= 0 and y1 >= 0 and x2 <= SHEET_W + 1e-6, "part outside the sheet"
    for c in C:
        near = (min(max(c[0], x1), x2), min(max(c[1], y1), y2))
        assert math.dist(near, c) >= OD / 2 + CLEAR, "part too close to a flange"
loose = [p for p in placed if not p[4]]
for i, p in enumerate(loose):
    for q in loose[i + 1:]:
        assert (p[2] + CLEAR <= q[0] or q[2] + CLEAR <= p[0] or
                p[3] + CLEAR <= q[1] or q[3] + CLEAR <= p[1]), "parts overlap"

with open("spool.svg", "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W:.2f}mm" height="{SHEET_H:.2f}mm" '
            f'viewBox="0 0 {SHEET_W:.2f} {SHEET_H:.2f}">\n' + "\n".join(out) + "\n</svg>\n")
print(f"spool.svg  {SHEET_W:.0f} x {SHEET_H:.0f} mm  (flange {OD:.0f}, rib {RIB_L:.1f} x {RIB_W:.2f}, clip {CLIP_L:.0f} x {CLIP_W:.1f})")
