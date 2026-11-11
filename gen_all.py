#!/usr/bin/env python3
"""One tightly nested sheet with a complete spool. Output: komplett.svg (mm).
Nothing lies outside the bounding box of the two staggered flanges:
- all 6 ribs lie flat in the corner under flange 1
- the 6 clips sit inside the two bore discs (waste anyway), 3 per bore
Runs the three generators first, then checks every placed part for clearance."""
import math, re, subprocess, sys
for g in ("gen_spule.py", "gen_riegel.py", "gen_clip.py"):
    subprocess.run([sys.executable, g], check=True)

OD, BORE, SHEET_W, GAP = 200.0, 55.0, 391.0, 2.0
DX = SHEET_W - OD
DY = math.ceil(math.sqrt((OD + GAP)**2 - DX**2))
F1, F2 = (OD/2, OD/2), (OD/2 + DX, OD/2 + DY)       # flange centres, same as gen_spule.py
W, H = SHEET_W, OD + DY
NUM = r"(-?[\d.]+),(-?[\d.]+)"

def read(name):
    return re.findall(r"<(?:path|rect|circle|line|polyline)[^>]*/>", open(name).read())

def pts(e):
    return [(float(a), float(b)) for a, b in re.findall(NUM, e)]

def bbox(els):
    p = [q for e in els for q in pts(e)]
    return min(x for x, _ in p), min(y for _, y in p), max(x for x, _ in p), max(y for _, y in p)

def place(els, x0, y0, rot=False):
    """Move elements so their bbox starts at (x0, y0); rot turns them 90 deg first."""
    bx, by, _, by2 = bbox(els)
    def f(m):
        x, y = float(m.group(1)) - bx, float(m.group(2)) - by
        if rot:
            x, y = (by2 - by) - y, x
        return f"{x0+x:.3f},{y0+y:.3f}"
    return [re.sub(NUM, f, e) for e in els]

spule = read("spule.svg")
ribs_plain = [e for e in spule if e.startswith("<path") and min(y for _, y in pts(e)) >= OD + 1]
flanges = [e for e in spule if e not in ribs_plain]
riegel = read("riegel.svg")
clips = read("clips.svg")
assert len(ribs_plain) == 3 and len(riegel) == 3 and len(clips) == 6

out, placed = list(flanges), []
def put(els, x, y, rot=False, inside=None):
    new = place(els, x, y, rot)
    out.extend(new)
    placed.append((bbox(new), inside))

# ribs, lying flat, in rows under flange 1
ROW, Y0 = 12.75 + GAP, OD + 3
LR = bbox(riegel[:1]); LR = LR[3] - LR[1]            # lockable rib length
put(riegel[0:1], 0, Y0, rot=True)
put(riegel[1:2], LR + GAP, Y0, rot=True)
put(riegel[2:3], 0, Y0 + ROW, rot=True)
put(ribs_plain[0:1], LR + GAP, Y0 + ROW, rot=True)
put(ribs_plain[1:2], 0, Y0 + 2 * ROW, rot=True)
put(ribs_plain[2:3], 66 + GAP, Y0 + 2 * ROW, rot=True)

# clips: 3 stacked per bore, centred on the flange centre
cb = bbox(clips[:1]); cl, cw = cb[2] - cb[0], cb[3] - cb[1]
for c, group in ((F1, clips[0:3]), (F2, clips[3:6])):
    for i, e in enumerate(group):
        put([e], c[0] - cl / 2, c[1] - (3 * cw + 2 * GAP) / 2 + i * (cw + GAP), inside=c)

# clearance check: 1.5 mm to every flange edge / bore edge, parts inside the sheet, no overlaps
for (x1, y1, x2, y2), inside in placed:
    corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
    if inside:
        assert max(math.dist(p, inside) for p in corners) <= BORE / 2 - 1.5, "clip block too big for bore"
        continue
    assert x1 >= 0 and y1 >= 0 and x2 <= W and y2 <= H, "part outside sheet"
    for c in (F1, F2):
        nearest = (min(max(c[0], x1), x2), min(max(c[1], y1), y2))
        assert math.dist(nearest, c) >= OD / 2 + 1.5, f"part at {x1:.0f},{y1:.0f} too close to a flange"
free = [b for b, i in placed if not i]
for i, a in enumerate(free):
    for b in free[i+1:]:
        assert a[2] + 1.5 <= b[0] or b[2] + 1.5 <= a[0] or a[3] + 1.5 <= b[1] or b[3] + 1.5 <= a[1], "ribs overlap"

open("komplett.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H:.2f}mm" '
                                f'viewBox="0 0 {W} {H:.2f}">\n' + "\n".join(out) + "\n</svg>\n")
bottom = max(b[3] for b in free)
print(f"komplett.svg {W} x {H:.0f} mm, ribs end at y {bottom:.1f}, checks passed")
