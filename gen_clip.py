#!/usr/bin/env python3
"""Snap-on clips for the spool ribs (replace the loose fork keys). Output: clips.svg (mm).
Two legs flex open over the 4 mm neck, then a square hook behind the throat holds it.
v3: longer legs (more flex) so the throat can be tighter and the hook square instead of ramped.
v4: seat is now SMALLER than the neck, so the legs stay sprung and clamp it; tighter throat, no play
    along the neck; legs longer again so the bigger opening does not snap them.
v5: bigger hook at the mouth (the tooth that wraps behind the neck): deeper step and longer land;
    legs a bit longer for the extra opening. Count via env CLIP_N (default 6)."""
import os
KERF = 0.2
NECK = 4.0               # rib neck width the clip grabs
T = 3.0                  # material thickness = neck depth in clip direction
THROAT = NECK - 1.7      # cut size, neck must snap past this (v2: -0.6, v3: -1.0, v4: -1.4)
SEAT = NECK - 0.5        # cut size where the neck rests; below NECK = permanent clamp (v3: NECK + 0.2)
LEG = 3.4                # leg width, thinner = easier snap / weaker (v2: 2.5, v3: 3.0)
L = 36.0                 # total length, longer = more flex (v2: 24, v3: 30, v4: 34)
N = int(os.environ.get("CLIP_N", 6))   # one per rib end, no spares
SP = 2.0
S = 'fill="none" stroke="#ff0000" stroke-width="0.1"'
k = KERF / 2
t, s, m, slit = THROAT/2 - k, SEAT/2 - k, SEAT/2 + 0.5, 0.5 - k
jaw, leg = SEAT/2 + LEG, 0.5 + LEG
RAMP, LAND = 2.5, 2.1                 # entry ramp length, throat land length (v4: 1.5)
x_hook = RAMP + LAND                  # square step: throat -> seat
x_seat = x_hook + T + 0.1             # seat end (v3: T + 0.4)
# upper half, from mouth (x=0) along the inside to the slit end, then back along the outside
inner = [(0, m), (RAMP, t), (x_hook, t), (x_hook, s), (x_seat, s), (x_seat + 0.4, slit), (L - 4, slit)]
outer = [(L, jaw), (L - 2.5, jaw), (L - 3.5, leg), (x_seat + 1.5, leg), (x_seat + 0.5, jaw), (0, jaw)]
W = 2 * jaw
out = []
def clip(x, y):
    up = [(px, -py) for px, py in inner]                      # top inside, mouth -> slit end
    down = [(px, py) for px, py in reversed(inner)]            # bottom inside, slit end -> mouth
    bot_out = [(px, py) for px, py in reversed(outer)]         # bottom outside, mouth -> base
    top_out = [(px, -py) for px, py in outer]                  # top outside, base -> mouth
    pts = up + down + bot_out + top_out
    d = "M" + " L".join(f"{x+px:.3f},{y+W/2+py:.3f}" for px, py in pts) + " Z"
    out.append(f'<path d="{d}" {S}/>')
for i in range(N):
    clip((i % 2) * (L + SP), (i // 2) * (W + SP))
TW, TH = 2 * L + SP, ((N + 1) // 2) * (W + SP) - SP
open("clips.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{TW}mm" height="{TH:.2f}mm" '
                             f'viewBox="0 0 {TW} {TH:.2f}">\n' + "\n".join(out) + "\n</svg>\n")
print(f"clips.svg {TW} x {TH:.1f} mm, clip {L} x {W:.1f}")
