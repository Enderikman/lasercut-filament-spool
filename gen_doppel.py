#!/usr/bin/env python3
"""Two complete spools on one 510 x 320 mm board, cut in two jobs with a board move in between.
Usable xTool S1 area is 498 x 297 (grey strip Y 0-21.5 is rejected by framing), the board is taller.
  doppel_A.svg  job 1: top flanges 1+3, all 12 ribs, 18 clips        (board y 0..~270)
  doppel_B.svg  job 2: bottom flanges 2+4 with 6 clips               (board y 144..318)
All 12 ribs are lockable ones (no plain push-in ribs), so each spool needs 12 clips, 24 in total:
3 per bore disc (12) plus 12 loose ones packed into the bottom-left corner.
The bottom flanges sit FGAP away from the top ones, so the board move only has to be right to ~4 mm.
Coordinates in both files are board coordinates; the script prints where to put each job on the bed."""
import math, os, re, subprocess, sys
OD = 174.0
os.environ["SPULE_OD"] = str(OD)
import gen_spule as s
for g in ("gen_riegel.py", "gen_clip.py"):
    subprocess.run([sys.executable, g], check=True)

GAP = 2.0
DX, DY = 107.3, 144.0
C = [(OD/2 + i * DX, OD/2 + (i % 2) * DY) for i in range(4)]   # 0,2 = top row, 1,3 = bottom row
FGAP = math.dist(C[0], C[1]) - OD
BED_Y0, BED_H, MOVE = 22.0, 297.0, 25.0                       # usable top, usable height, board move
NUM = r"(-?[\d.]+),(-?[\d.]+)"

def bbox(els):
    p = [(float(a), float(b)) for e in els for a, b in re.findall(NUM, e)]
    return min(x for x, _ in p), min(y for _, y in p), max(x for x, _ in p), max(y for _, y in p)

def moved(e, x0, y0):
    bx, by, _, _ = bbox([e])
    return re.sub(NUM, lambda m: f"{x0+float(m.group(1))-bx:.3f},{y0+float(m.group(2))-by:.3f}", e)

def flange_els(i):
    s.out.clear()
    s.flange(C[i][0], C[i][1], with_gauge=(i in (0, 1)))       # one gauge flange per job
    return list(s.out)

read = lambda n: re.findall(r"<path[^>]*/>", open(n).read())
s.out.clear(); s.rib(0, 0); plain = s.out.pop()
riegel, clips = read("riegel.svg") * 4, read("clips.svg") * 4
PITCH = s.rib_h + GAP
ribs = []                                                      # (element, x, y)
x_tr = C[2][0] + OD/2 + GAP                                    # top-right corner, right of flange 3
for i in range(7):
    ribs.append((riegel[i], x_tr + i * PITCH, 0))
x_gap = (C[0][0] + C[2][0]) / 2 - (2 * s.rib_h + GAP) / 2      # gap between the two top flanges
for i in range(2):
    ribs.append((riegel[7 + i], x_gap + i * PITCH, 0))
for i in range(3):                                             # bottom-left corner, under flange 1
    ribs.append((riegel[9 + i], i * PITCH, OD + 3))
rib_els = [moved(e, x, y) for e, x, y in ribs]

def clip_els(k, c):
    cb = bbox(clips[:1]); cl, cw = cb[2] - cb[0], cb[3] - cb[1]
    return [moved(clips[3*k + i], c[0] - cl/2, c[1] - (3*cw + 2*GAP)/2 + i * (cw + GAP)) for i in range(3)]

for e in rib_els:                                              # clearance to all four flanges, no overlaps
    x1, y1, x2, y2 = bbox([e])
    assert x1 >= 0 and y1 >= 0
    for c in C:
        near = (min(max(c[0], x1), x2), min(max(c[1], y1), y2))
        assert math.dist(near, c) >= OD/2 + 1.5, f"rib at {x1:.0f},{y1:.0f} hits a flange"
bb = [bbox([e]) for e in rib_els]
for i, a in enumerate(bb):
    for b in bb[i+1:]:
        assert a[2] + 1.5 <= b[0] or b[2] + 1.5 <= a[0] or a[3] + 1.5 <= b[1] or b[3] + 1.5 <= a[1], "ribs overlap"
assert FGAP >= 4, "flange gap too small for a hand-moved board"

# 12 loose clips: greedy scan of the bottom-left corner, keeping clear of flanges, ribs and each other
cb = bbox(clips[:1]); CL, CW = cb[2] - cb[0], cb[3] - cb[1]
Y_MAX_A = BED_H - 2                                            # job A must stay on the bed
loose, taken = [], list(bb)
def free(x, y):
    r = (x, y, x + CL, y + CW)
    if r[3] > Y_MAX_A: return False
    for c in C:
        near = (min(max(c[0], r[0]), r[2]), min(max(c[1], r[1]), r[3]))
        if math.dist(near, c) < OD/2 + 1.5: return False
    return all(r[2] + 1.5 <= t[0] or t[2] + 1.5 <= r[0] or r[3] + 1.5 <= t[1] or t[3] + 1.5 <= r[1] for t in taken)
y = OD + 3
while y <= Y_MAX_A - CW and len(loose) < 12:
    x = 0.0
    while x <= 140 and len(loose) < 12:
        if free(x, y):
            loose.append(moved(clips[12 + len(loose)], x, y)); taken.append((x, y, x + CL, y + CW)); x += CL + GAP
        else:
            x += 1.0
    y += 1.0
assert len(loose) == 12, f"only {len(loose)} loose clips fit"

def save(name, els, x1, y1, x2, y2):
    w, h = x2 - x1, y2 - y1
    body = "\n".join(els)
    open(name, "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h:.2f}mm" '
                          f'viewBox="{x1:.2f} {y1:.2f} {w:.2f} {h:.2f}">\n{body}\n</svg>\n')
    return w, h

A = flange_els(0) + flange_els(2) + clip_els(0, C[0]) + clip_els(2, C[2]) + rib_els + loose
ax2, ay2 = max(b[2] for b in taken), max(max(b[3] for b in taken), OD)
wa, ha = save("doppel_A.svg", A, 0, 0, ax2, ay2)
B = flange_els(1) + flange_els(3) + clip_els(1, C[1]) + clip_els(3, C[3])
bx1, by1, bx2, by2 = C[1][0] - OD/2, C[1][1] - OD/2, C[3][0] + OD/2, C[3][1] + OD/2
wb, hb = save("doppel_B.svg", B, bx1, by1, bx2, by2)
X0 = 1.0
assert X0 + ax2 <= 497 and BED_Y0 + ay2 <= BED_Y0 + BED_H
yb = BED_Y0 + by1 - MOVE
assert X0 + bx2 <= 497.5 and yb + hb <= BED_Y0 + BED_H
print(f"flange {OD}, gap between top and bottom flanges {FGAP:.1f} mm")
print(f"job A doppel_A.svg {wa:.1f} x {ha:.1f} -> bed X {X0} Y {BED_Y0}")
print(f"job B doppel_B.svg {wb:.1f} x {hb:.1f} -> move board {MOVE:.0f} mm towards Y=0, then bed X {X0+bx1:.1f} Y {yb:.1f}")
