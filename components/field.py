import math
import numpy as np
from .loaders import get_jugadores, get_pos, get_pid, get_team
from .overlays import convex_hull, centroide, voronoi_simple, superioridad_zonas

FIELD_W = 50
FIELD_H = 30

TEAM_COLORS = {0: "#E8593C", 1: "#3B8BD4", -1: "#888780"}
TEAM_COLORS_A = {
    0: "rgba(232,89,60,{a})",
    1: "rgba(59,139,212,{a})",
    -1: "rgba(136,135,128,{a})",
}
TEAM_NAMES = {0: "Equipo 1", 1: "Equipo 2", -1: "Sin equipo"}

SVG_W, SVG_H = 680, 408
PAD_L, PAD_T = 36, 28
DRAW_W = SVG_W - PAD_L - 36
DRAW_H = SVG_H - PAD_T - 28


def field_to_px(x, y):
    return (PAD_L + (x / FIELD_W) * DRAW_W,
            PAD_T + (y / FIELD_H) * DRAW_H)


def color_a(team, alpha):
    return TEAM_COLORS_A.get(team, "rgba(136,135,128,{a})").format(a=alpha)


def pts_to_svg_poly(pts_field):
    return " ".join(
        f"{field_to_px(x,y)[0]:.1f},{field_to_px(x,y)[1]:.1f}"
        for x, y in pts_field
    )


def _draw_base_field(lines):
    """Líneas del campo: borde, medio campo, círculo central, áreas."""
    def ln(x1, y1, x2, y2, **kw):
        p1 = field_to_px(x1, y1); p2 = field_to_px(x2, y2)
        attrs = " ".join(f'{k}="{v}"' for k, v in kw.items())
        lines.append(
            f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" '
            f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" {attrs}/>'
        )

    tl = field_to_px(0, 0); br = field_to_px(FIELD_W, FIELD_H)
    lines.append(
        f'<rect x="{tl[0]}" y="{tl[1]}" width="{br[0]-tl[0]}" height="{br[1]-tl[1]}" '
        f'fill="none" stroke="rgba(255,255,255,0.65)" stroke-width="2"/>'
    )
    ln(FIELD_W/2, 0, FIELD_W/2, FIELD_H,
       stroke="rgba(255,255,255,0.55)", **{"stroke-width": "1.5"})
    cc = field_to_px(FIELD_W/2, FIELD_H/2)
    rx = 4.5/FIELD_W*DRAW_W; ry = 4.5/FIELD_H*DRAW_H
    lines.append(
        f'<ellipse cx="{cc[0]:.1f}" cy="{cc[1]:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
        f'fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="1.5"/>'
    )
    lines.append(
        f'<circle cx="{cc[0]:.1f}" cy="{cc[1]:.1f}" r="3" fill="rgba(255,255,255,0.55)"/>'
    )
    for side in [0, FIELD_W]:
        s = 1 if side == 0 else -1
        x2 = side + s*10; y1f = FIELD_H/2-6; y2f = FIELD_H/2+6
        for a, b in [(side, y1f, x2, y1f), (x2, y1f, x2, y2f), (x2, y2f, side, y2f)]:
            ln(a, b[0] if isinstance(b, tuple) else a,
               b if not isinstance(b, tuple) else b[0],
               b if not isinstance(b, tuple) else b[1],
               stroke="rgba(255,255,255,0.55)", **{"stroke-width": "1.5"})
        # simpler:
    lines.pop(); lines.pop(); lines.pop()  # remove malformed, redo
    for side in [0, FIELD_W]:
        s = 1 if side == 0 else -1
        x2v = side + s*10; y1f = FIELD_H/2-6; y2f = FIELD_H/2+6
        for (ax, ay, bx, by) in [
            (side, y1f, x2v, y1f),
            (x2v, y1f, x2v, y2f),
            (x2v, y2f, side, y2f),
        ]:
            p1 = field_to_px(ax, ay); p2 = field_to_px(bx, by)
            lines.append(
                f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" '
                f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                f'stroke="rgba(255,255,255,0.55)" stroke-width="1.5"/>'
            )


def build_field_svg(jugadores, ovs, trajs=None, frame_idx=0,
                    heatmap_data=None, heatmap_team=None,
                    heatmap_diff=None, player_team=None,
                    frames_data=None):

    e0 = [j for j in jugadores if get_team(j) == 0]
    e1 = [j for j in jugadores if get_team(j) == 1]
    pts0 = [get_pos(j) for j in e0]
    pts1 = [get_pos(j) for j in e1]
    all_pts = pts0 + pts1

    lines = []
    lines.append(
        f'<svg width="{SVG_W}" height="{SVG_H}" xmlns="http://www.w3.org/2000/svg" '
        f'style="background:#2d6a1f;border-radius:8px;width:100%">'
    )

    _draw_base_field(lines)

    # ── Heatmap diferencial ───────────────────────────────────
    if ovs.get("heatmap_diff") and heatmap_diff:
        gw, gh = 20, 12
        grid_e0 = np.zeros((gh, gw)); grid_e1 = np.zeros((gh, gw))
        for x, y in heatmap_diff.get("e0", []):
            gx = min(int(x/FIELD_W*gw), gw-1)
            gy = min(int(y/FIELD_H*gh), gh-1)
            grid_e0[gy, gx] += 1
        for x, y in heatmap_diff.get("e1", []):
            gx = min(int(x/FIELD_W*gw), gw-1)
            gy = min(int(y/FIELD_H*gh), gh-1)
            grid_e1[gy, gx] += 1
        mx = max(grid_e0.max(), grid_e1.max(), 1)
        cw_px = DRAW_W/gw; ch_px = DRAW_H/gh
        for gy in range(gh):
            for gx in range(gw):
                diff = (grid_e0[gy, gx] - grid_e1[gy, gx]) / mx
                if abs(diff) > 0.05:
                    col = (f"rgba(232,89,60,{abs(diff)*0.6:.2f})" if diff > 0
                           else f"rgba(59,139,212,{abs(diff)*0.6:.2f})")
                    px_x = PAD_L + gx*cw_px; px_y = PAD_T + gy*ch_px
                    lines.append(
                        f'<rect x="{px_x:.1f}" y="{px_y:.1f}" '
                        f'width="{cw_px:.1f}" height="{ch_px:.1f}" '
                        f'fill="{col}" rx="2"/>'
                    )

    # ── Heatmap por equipo ────────────────────────────────────
    if ovs.get("heatmap_equipo") and heatmap_data:
        gw, gh = 25, 15
        grid = np.zeros((gh, gw))
        for x, y in heatmap_data:
            gx = min(int(x/FIELD_W*gw), gw-1)
            gy = min(int(y/FIELD_H*gh), gh-1)
            grid[gy, gx] += 1
        mx = grid.max() or 1
        cw_px = DRAW_W/gw; ch_px = DRAW_H/gh
        for gy in range(gh):
            for gx in range(gw):
                v = grid[gy, gx] / mx
                if v < 0.05: continue
                px_x = PAD_L + gx*cw_px; px_y = PAD_T + gy*ch_px
                lines.append(
                    f'<rect x="{px_x:.1f}" y="{px_y:.1f}" '
                    f'width="{cw_px:.1f}" height="{ch_px:.1f}" '
                    f'fill="{color_a(heatmap_team, v*0.65)}" rx="2"/>'
                )

    # ── Voronoi ───────────────────────────────────────────────
    if ovs.get("voronoi") and pts0 and pts1:
        for gx, gy, team, cw_f, ch_f in voronoi_simple(pts0, pts1):
            p = field_to_px(gx*cw_f, gy*ch_f)
            pw = cw_f/FIELD_W*DRAW_W; ph = ch_f/FIELD_H*DRAW_H
            lines.append(
                f'<rect x="{p[0]:.1f}" y="{p[1]:.1f}" '
                f'width="{pw:.1f}" height="{ph:.1f}" '
                f'fill="{color_a(team, 0.22)}"/>'
            )

    # ── Superioridad por zonas ────────────────────────────────
    if ovs.get("superioridad"):
        for x0f, y0f, x1f, y1f, n0, n1 in superioridad_zonas(pts0, pts1):
            if n0 == n1: continue
            team = 0 if n0 > n1 else 1
            p0 = field_to_px(x0f, y0f); p1 = field_to_px(x1f, y1f)
            lines.append(
                f'<rect x="{p0[0]:.1f}" y="{p0[1]:.1f}" '
                f'width="{p1[0]-p0[0]:.1f}" height="{p1[1]-p0[1]:.1f}" '
                f'fill="{color_a(team, 0.3)}" '
                f'stroke="{TEAM_COLORS[team]}" stroke-width="0.5" rx="3"/>'
            )
            cx_px = (p0[0]+p1[0])/2; cy_px = (p0[1]+p1[1])/2
            lines.append(
                f'<text x="{cx_px:.1f}" y="{cy_px+4:.1f}" text-anchor="middle" '
                f'font-size="11" fill="{TEAM_COLORS[team]}" '
                f'font-weight="500">+{abs(n0-n1)}</text>'
            )

    # ── Polígono convexo ──────────────────────────────────────
    if ovs.get("poligono_convexo"):
        for pts, team in [(pts0, 0), (pts1, 1)]:
            if len(pts) >= 3:
                hull = convex_hull(pts)
                lines.append(
                    f'<polygon points="{pts_to_svg_poly(hull)}" '
                    f'fill="{color_a(team, 0.15)}" '
                    f'stroke="{TEAM_COLORS[team]}" stroke-width="1.5"/>'
                )

    # ── Rectángulo de bloque ──────────────────────────────────
    if ovs.get("rectangulo_bloque"):
        for pts, team in [(pts0, 0), (pts1, 1)]:
            if len(pts) >= 2:
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                p0 = field_to_px(min(xs), min(ys))
                p1 = field_to_px(max(xs), max(ys))
                lines.append(
                    f'<rect x="{p0[0]:.1f}" y="{p0[1]:.1f}" '
                    f'width="{p1[0]-p0[0]:.1f}" height="{p1[1]-p0[1]:.1f}" '
                    f'fill="{color_a(team, 0.1)}" '
                    f'stroke="{TEAM_COLORS[team]}" stroke-width="1.5" '
                    f'stroke-dasharray="5 3" rx="3"/>'
                )

    # ── Espacio libre ─────────────────────────────────────────
    if ovs.get("espacio_libre") and all_pts:
        grid = 12; cw_f = FIELD_W/grid; ch_f = FIELD_H/grid
        for gx in range(grid):
            for gy in range(grid):
                cx = (gx+0.5)*cw_f; cy = (gy+0.5)*ch_f
                d_min = min(math.hypot(cx-x, cy-y) for x, y in all_pts)
                if d_min > 5:
                    p = field_to_px(gx*cw_f, gy*ch_f)
                    pw = cw_f/FIELD_W*DRAW_W; ph = ch_f/FIELD_H*DRAW_H
                    v = min((d_min-5)/10, 1)
                    lines.append(
                        f'<rect x="{p[0]:.1f}" y="{p[1]:.1f}" '
                        f'width="{pw:.1f}" height="{ph:.1f}" '
                        f'fill="rgba(250,204,21,{v*0.35:.2f})" rx="2"/>'
                    )

    # ── Espacio entre líneas defensivas ───────────────────────
    if ovs.get("espacio_lineas") and pts0 and pts1:
        ld_e0 = max(p[0] for p in pts0)
        ld_e1 = min(p[0] for p in pts1)
        if ld_e0 < ld_e1:
            p0 = field_to_px(ld_e0, 0); p1 = field_to_px(ld_e1, FIELD_H)
            lines.append(
                f'<rect x="{p0[0]:.1f}" y="{p0[1]:.1f}" '
                f'width="{p1[0]-p0[0]:.1f}" height="{p1[1]-p0[1]:.1f}" '
                f'fill="rgba(250,204,21,0.12)" '
                f'stroke="rgba(250,204,21,0.4)" stroke-width="1" stroke-dasharray="4 3"/>'
            )
            cx_px = (p0[0]+p1[0])/2; cy_px = (p0[1]+p1[1])/2
            lines.append(
                f'<text x="{cx_px:.1f}" y="{cy_px+4:.1f}" text-anchor="middle" '
                f'font-size="9" fill="rgba(250,204,21,0.8)">espacio</text>'
            )

    # ── Línea defensiva ───────────────────────────────────────
    if ovs.get("linea_defensiva"):
        for pts, team, fn in [(pts0, 0, min), (pts1, 1, max)]:
            if pts:
                x_def = fn(p[0] for p in pts)
                p = field_to_px(x_def, 0); p2 = field_to_px(x_def, FIELD_H)
                lines.append(
                    f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" '
                    f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                    f'stroke="{TEAM_COLORS[team]}" stroke-width="1.5" stroke-dasharray="5 3"/>'
                )
                lines.append(
                    f'<text x="{p[0]+4:.1f}" y="{p[1]+14:.1f}" font-size="9" '
                    f'fill="{TEAM_COLORS[team]}">línea def E{team+1}</text>'
                )

    # ── Línea de presión ──────────────────────────────────────
    if ovs.get("linea_presion"):
        for pts, team, fn in [(pts0, 0, max), (pts1, 1, min)]:
            if pts:
                x_pre = fn(p[0] for p in pts)
                p = field_to_px(x_pre, 0); p2 = field_to_px(x_pre, FIELD_H)
                lines.append(
                    f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" '
                    f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                    f'stroke="{TEAM_COLORS[team]}" stroke-width="1" '
                    f'stroke-dasharray="2 4" opacity="0.7"/>'
                )

    # ── Líneas de banda ───────────────────────────────────────
    if ovs.get("lineas_banda"):
        for pts, team in [(pts0, 0), (pts1, 1)]:
            if len(pts) >= 2:
                ys = [p[1] for p in pts]
                for y_val in [min(ys), max(ys)]:
                    p = field_to_px(0, y_val); p2 = field_to_px(FIELD_W, y_val)
                    lines.append(
                        f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" '
                        f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                        f'stroke="{TEAM_COLORS[team]}" stroke-width="1" '
                        f'stroke-dasharray="3 4" opacity="0.5"/>'
                    )

    # ── Red de proximidad ─────────────────────────────────────
    if ovs.get("red_proximidad"):
        DIST_MAX = 15
        for pts, team in [(pts0, 0), (pts1, 1)]:
            for i in range(len(pts)):
                for j in range(i+1, len(pts)):
                    d = math.hypot(pts[i][0]-pts[j][0], pts[i][1]-pts[j][1])
                    if d < DIST_MAX:
                        p1 = field_to_px(*pts[i]); p2 = field_to_px(*pts[j])
                        alpha = max(0.1, 0.5*(1-d/DIST_MAX))
                        lines.append(
                            f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" '
                            f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                            f'stroke="{TEAM_COLORS[team]}" stroke-width="1" '
                            f'opacity="{alpha:.2f}"/>'
                        )

    # ── Triángulos de juego ───────────────────────────────────
    if ovs.get("triangulos"):
        for pts, team in [(pts0, 0), (pts1, 1)]:
            if len(pts) >= 3:
                cx, cy = centroide(pts)
                tri = sorted(pts, key=lambda p: math.hypot(p[0]-cx, p[1]-cy))[:3]
                lines.append(
                    f'<polygon points="{pts_to_svg_poly(tri)}" '
                    f'fill="{color_a(team, 0.12)}" '
                    f'stroke="{TEAM_COLORS[team]}" stroke-width="1" '
                    f'stroke-dasharray="3 2" opacity="0.8"/>'
                )

    # ── Marcajes más cercanos ─────────────────────────────────
    if ovs.get("marcajes") and pts0 and pts1:
        for p0 in pts0:
            closest = min(pts1, key=lambda p: math.hypot(p0[0]-p[0], p0[1]-p[1]))
            pp0 = field_to_px(*p0); pp1 = field_to_px(*closest)
            d = math.hypot(p0[0]-closest[0], p0[1]-closest[1])
            alpha = max(0.15, min(0.6, 8/max(d, 1)))
            lines.append(
                f'<line x1="{pp0[0]:.1f}" y1="{pp0[1]:.1f}" '
                f'x2="{pp1[0]:.1f}" y2="{pp1[1]:.1f}" '
                f'stroke="rgba(250,204,21,{alpha:.2f})" stroke-width="1" '
                f'stroke-dasharray="2 3"/>'
            )

    # ── Radio de presión ──────────────────────────────────────
    if ovs.get("radio_presion"):
        RADIO = 8
        for pts, team in [(pts0, 0), (pts1, 1)]:
            for x, y in pts:
                p = field_to_px(x, y)
                rx = RADIO/FIELD_W*DRAW_W; ry = RADIO/FIELD_H*DRAW_H
                lines.append(
                    f'<ellipse cx="{p[0]:.1f}" cy="{p[1]:.1f}" '
                    f'rx="{rx:.1f}" ry="{ry:.1f}" '
                    f'fill="{color_a(team, 0.08)}" '
                    f'stroke="{TEAM_COLORS[team]}" stroke-width="0.5" opacity="0.5"/>'
                )

    # ── Centroide ─────────────────────────────────────────────
    if ovs.get("centroide"):
        for pts, team in [(pts0, 0), (pts1, 1)]:
            if pts:
                cx, cy = centroide(pts)
                p = field_to_px(cx, cy)
                lines.append(
                    f'<line x1="{p[0]-14:.1f}" y1="{p[1]:.1f}" '
                    f'x2="{p[0]+14:.1f}" y2="{p[1]:.1f}" '
                    f'stroke="{TEAM_COLORS[team]}" stroke-width="2.5" opacity="0.8"/>'
                )
                lines.append(
                    f'<line x1="{p[0]:.1f}" y1="{p[1]-14:.1f}" '
                    f'x2="{p[0]:.1f}" y2="{p[1]+14:.1f}" '
                    f'stroke="{TEAM_COLORS[team]}" stroke-width="2.5" opacity="0.8"/>'
                )
                rx = 10/FIELD_W*DRAW_W; ry = 10/FIELD_H*DRAW_H
                lines.append(
                    f'<ellipse cx="{p[0]:.1f}" cy="{p[1]:.1f}" '
                    f'rx="{rx:.1f}" ry="{ry:.1f}" fill="none" '
                    f'stroke="{TEAM_COLORS[team]}" stroke-width="1.5" '
                    f'stroke-dasharray="3 2" opacity="0.7"/>'
                )

    # ── Cola de trayectoria ───────────────────────────────────
    if ovs.get("cola") and frames_data and frame_idx > 0:
        from collections import defaultdict as dd
        TAIL = 8
        start = max(0, frame_idx - TAIL)
        tail_pts = dd(list)
        for fi in range(start, frame_idx + 1):
            for det in get_jugadores(frames_data[fi]):
                tail_pts[get_pid(det)].append((fi, get_pos(det), get_team(det)))
        for pid, pts_tail in tail_pts.items():
            if len(pts_tail) < 2: continue
            team = pts_tail[-1][2]
            for i in range(1, len(pts_tail)):
                alpha = 0.15 + 0.6*(i/len(pts_tail))
                p1 = field_to_px(*pts_tail[i-1][1])
                p2 = field_to_px(*pts_tail[i][1])
                sw = 0.5 + 1.5*(i/len(pts_tail))
                lines.append(
                    f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" '
                    f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                    f'stroke="{TEAM_COLORS[team]}" stroke-width="{sw:.1f}" '
                    f'opacity="{alpha:.2f}" stroke-linecap="round"/>'
                )

    # ── Vectores de velocidad ─────────────────────────────────
    if ovs.get("vectores") and frames_data and frame_idx > 0:
        prev_frame = {}
        for det in get_jugadores(frames_data[max(0, frame_idx-1)]):
            prev_frame[get_pid(det)] = get_pos(det)
        has_arrows = False
        for det in jugadores:
            pid = get_pid(det); x, y = get_pos(det)
            if pid in prev_frame:
                px_prev, py_prev = prev_frame[pid]
                dx = x - px_prev; dy = y - py_prev
                speed = math.hypot(dx, dy)
                if speed > 0.3:
                    if not has_arrows:
                        lines.insert(1, '<defs>'
                            f'<marker id="arr_0" viewBox="0 0 6 6" refX="5" refY="3" '
                            f'markerWidth="4" markerHeight="4" orient="auto">'
                            f'<path d="M0 0L6 3L0 6" fill="{TEAM_COLORS[0]}"/></marker>'
                            f'<marker id="arr_1" viewBox="0 0 6 6" refX="5" refY="3" '
                            f'markerWidth="4" markerHeight="4" orient="auto">'
                            f'<path d="M0 0L6 3L0 6" fill="{TEAM_COLORS[1]}"/></marker>'
                            '</defs>')
                        has_arrows = True
                    scale = min(speed*3, 8)
                    nx = dx/speed*scale; ny = dy/speed*scale
                    p_start = field_to_px(x, y)
                    p_end = field_to_px(x+nx, y+ny)
                    team = get_team(det)
                    lines.append(
                        f'<line x1="{p_start[0]:.1f}" y1="{p_start[1]:.1f}" '
                        f'x2="{p_end[0]:.1f}" y2="{p_end[1]:.1f}" '
                        f'stroke="{TEAM_COLORS[team]}" stroke-width="2" '
                        f'marker-end="url(#arr_{team})"/>'
                    )

    # ── Jugadores (siempre encima) ────────────────────────────
    for det in jugadores:
        if not isinstance(det, dict): continue
        x, y = get_pos(det)
        pid = get_pid(det)
        team = get_team(det)
        ppx, ppy = field_to_px(x, y)
        color = TEAM_COLORS.get(team, "#888")
        lines.append(
            f'<circle cx="{ppx:.1f}" cy="{ppy:.1f}" r="7" '
            f'fill="{color}" stroke="rgba(0,0,0,0.4)" stroke-width="1.5"/>'
        )
        lines.append(
            f'<text x="{ppx:.1f}" y="{ppy+4:.1f}" text-anchor="middle" '
            f'font-size="8" font-family="sans-serif" font-weight="bold" '
            f'fill="white">{pid}</text>'
        )

    lines.append('</svg>')
    return "\n".join(lines)
