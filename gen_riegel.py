#!/usr/bin/env python3
"""Lockable ribs for the laser-cut spool: 3 ribs with necked tabs + fork keys (Riegel).
Fits the existing flange slots (7 x 3 mm). Output: riegel.svg (mm). No glue needed."""
T = 3.0          # material thickness (measure your sheet!)
KERF = 0.15
BORE, HUB, INNER_W = 55.0, 80.5, 60.0
TAB = 7.0        # must match flange slot
NECK = 4.0       # neck width the fork grips
THROUGH = T + 0.15   # tab length inside the flange
GAP = T + 0.3        # notch length for the fork (cut size)
HEAD = 2.5
N_RIBS, N_KEYS = 3, 0    # fork keys dropped, snap clips (gen_clip.py) replace them
KEY_L, KEY_W, SLOT_L = 16.0, 12.0, 11.0
SLOT_MOUTH, SLOT_END = NECK + 0.15, NECK - 0.1   # tapered: jams onto the neck
SP = 2.0

S = 'fill="none" stroke="#ff0000" stroke-width="0.1"'
out = []
rib_h = (HUB - BORE) / 2
c = rib_h / 2
a, b = c - (TAB + KERF) / 2, c + (TAB + KERF) / 2
n1, n2 = c - (NECK + KERF) / 2, c + (NECK + KERF) / 2
gap = GAP - KERF
E = THROUGH + gap + HEAD
L = INNER_W + 2 * E

def path(pts, x, y):
    d = "M" + " L".join(f"{x+px:.3f},{y+py:.3f}" for px, py in pts) + " Z"
    out.append(f'<path d="{d}" {S}/>')

def rib(x, y):
    y1, y2 = E - THROUGH, E - THROUGH - gap      # notch start / head start
    top = [(0, E), (a, E), (a, y1), (n1, y1), (n1, y2), (a, y2), (a, 0.5), (a + 0.5, 0),
           (b - 0.5, 0), (b, 0.5), (b, y2), (n2, y2), (n2, y1), (b, y1), (b, E), (rib_h, E)]
    bottom = [(px, L - py) for px, py in reversed(top)]
    path(top + bottom, x, y)

def key(x, y):
    m, e = (SLOT_MOUTH - KERF) / 2, (SLOT_END - KERF) / 2
    h = KEY_W / 2
    path([(0, 0), (KEY_L, 0), (KEY_L, KEY_W), (0, KEY_W), (0, h + m), (SLOT_L, h + e),
          (SLOT_L, h - e), (0, h - m)], x, y)

for i in range(N_RIBS):
    rib(i * (rib_h + SP), 0)
x0 = N_RIBS * (rib_h + SP)
for i in range(N_KEYS):
    key(x0 + (i % 2) * (KEY_L + SP), (i // 2) * (KEY_W + SP))
W = x0 + 2 * KEY_L + SP if N_KEYS else x0 - SP
H = max(L, (N_KEYS // 2) * (KEY_W + SP))
open("riegel.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H:.2f}mm" '
    f'viewBox="0 0 {W} {H:.2f}">\n' + "\n".join(out) + "\n</svg>\n")
print(f"riegel.svg {W} x {H:.1f} mm; rib length {L:.1f}, sticks out {gap+HEAD:.2f} mm per side, total width {INNER_W+2*T+2*(E-T):.1f}")
