#!/usr/bin/env python3
"""Job B of the two-spool board with the flanges at positions aligned by hand in xTool Studio.
Edit LEFT / RIGHT (top-left corner of each Ø174 circle, bed mm), rerun. Output: doppel_B_pos.svg.
Paste it, then set the selection to the printed X / Y."""
import os, re
OD = 174.0
os.environ["SPULE_OD"] = str(OD)
import gen_spule as s
LEFT, RIGHT = (20.14, 23.49), (318.31, 87.06)      # read from the canvas after aligning to the cut board
GAP = 2.0
NUM = r"(-?[\d.]+),(-?[\d.]+)"
clips = re.findall(r"<path[^>]*/>", open("clips.svg").read())
assert len(clips) == 6
def bbox(e):
    p = [(float(a), float(b)) for a, b in re.findall(NUM, e)]
    return min(x for x, _ in p), min(y for _, y in p), max(x for x, _ in p), max(y for _, y in p)
def moved(e, x0, y0):
    bx, by, _, _ = bbox(e)
    return re.sub(NUM, lambda m: f"{x0+float(m.group(1))-bx:.3f},{y0+float(m.group(2))-by:.3f}", e)
cb = bbox(clips[0]); cl, cw = cb[2] - cb[0], cb[3] - cb[1]
s.out.clear()
els = []
for k, (x, y) in enumerate((LEFT, RIGHT)):
    c = (x + OD/2, y + OD/2)
    s.flange(c[0], c[1], with_gauge=(k == 0))
    els += [moved(clips[3*k + i], c[0] - cl/2, c[1] - (3*cw + 2*GAP)/2 + i * (cw + GAP)) for i in range(3)]
els = list(s.out) + els
x1, y1 = min(LEFT[0], RIGHT[0]), min(LEFT[1], RIGHT[1])
w, h = max(LEFT[0], RIGHT[0]) + OD - x1, max(LEFT[1], RIGHT[1]) + OD - y1
open("doppel_B_pos.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h:.2f}mm" '
                                    f'viewBox="{x1:.2f} {y1:.2f} {w:.2f} {h:.2f}">\n' + "\n".join(els) + "\n</svg>\n")
print(f"doppel_B_pos.svg {w:.2f} x {h:.2f} -> bed X {x1} Y {y1}")
