import math
import numpy as np


def convex_hull(pts):
    if len(pts) < 3:
        return pts
    pts = sorted(set(pts))

    def cross(O, A, B):
        return (A[0]-O[0])*(B[1]-O[1]) - (A[1]-O[1])*(B[0]-O[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def centroide(pts):
    if not pts:
        return None, None
    return float(np.mean([p[0] for p in pts])), float(np.mean([p[1] for p in pts]))


def voronoi_simple(pts_e0, pts_e1, grid=18, field_w=50, field_h=30):
    cells = []
    cw = field_w / grid
    ch = field_h / grid
    for gx in range(grid):
        for gy in range(grid):
            cx = (gx + 0.5) * cw
            cy = (gy + 0.5) * ch
            d0 = min((math.hypot(cx-x, cy-y) for x, y in pts_e0), default=999)
            d1 = min((math.hypot(cx-x, cy-y) for x, y in pts_e1), default=999)
            cells.append((gx, gy, 0 if d0 < d1 else 1, cw, ch))
    return cells


def superioridad_zonas(pts_e0, pts_e1, cols=3, rows=2, field_w=50, field_h=30):
    cw = field_w / cols
    ch = field_h / rows
    zonas = []
    for c in range(cols):
        for r in range(rows):
            x0 = c*cw; y0 = r*ch; x1 = x0+cw; y1 = y0+ch
            n0 = sum(1 for x, y in pts_e0 if x0 <= x < x1 and y0 <= y < y1)
            n1 = sum(1 for x, y in pts_e1 if x0 <= x < x1 and y0 <= y < y1)
            zonas.append((x0, y0, x1, y1, n0, n1))
    return zonas
