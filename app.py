import streamlit as st
import json
import numpy as np
import math
import zipfile
import io
from collections import defaultdict
from PIL import Image

st.set_page_config(
    page_title="Análisis táctico 7x7",
    page_icon="⚽",
    layout="wide"
)

FIELD_W = 50
FIELD_H = 30
TEAM_COLORS = {0: "#E8593C", 1: "#3B8BD4", -1: "#888780"}
TEAM_NAMES  = {0: "Equipo 1", 1: "Equipo 2", -1: "Sin equipo"}

# ── helpers ───────────────────────────────────────────────────────────────────

def load_zip(uploaded):
    frames = None
    frame_images = {}
    with zipfile.ZipFile(io.BytesIO(uploaded.read())) as z:
        for name in z.namelist():
            if name.endswith(".json"):
                with z.open(name) as f:
                    raw = json.load(f)
                    def safe_key(x):
                        try: return int(x)
                        except: return x
                    frames = raw if isinstance(raw, list) else [raw[k] for k in sorted(raw, key=safe_key)]
            elif name.lower().endswith((".jpg", ".jpeg", ".png")):
                # nombre esperado: frame_000123.jpg → índice 123
                stem = name.split("/")[-1].rsplit(".", 1)[0]
                digits = "".join(c for c in stem if c.isdigit())
                if digits:
                    idx = int(digits)
                    with z.open(name) as f:
                        frame_images[idx] = Image.open(io.BytesIO(f.read())).convert("RGB")
    return frames, frame_images

def build_trajectories(frames):
    trajs = defaultdict(list)
    for fi, frame in enumerate(frames):
        if not isinstance(frame, list):
            continue
        for det in frame:
            pid  = det.get("id", det.get("pid", -1))
            x    = det.get("x_campo", det.get("x", 0))
            y    = det.get("y_campo", det.get("y", 0))
            team = det.get("equipo", det.get("team", -1))
            trajs[pid].append((fi, x, y, team))
    return trajs

def distance_per_player(trajs):
    result = {}
    for pid, pts in trajs.items():
        d = 0.0
        for i in range(1, len(pts)):
            dx = pts[i][1] - pts[i-1][1]
            dy = pts[i][2] - pts[i-1][2]
            d += math.sqrt(dx*dx + dy*dy)
        result[pid] = round(d, 1)
    return result

def majority_team(pts):
    from collections import Counter
    c = Counter(p[3] for p in pts)
    return c.most_common(1)[0][0]

# ── SVG field ──────────────────────────────────────────────────────────────────

SVG_W, SVG_H = 680, 408
PAD_L, PAD_T = 36, 28
DRAW_W = SVG_W - PAD_L - 36
DRAW_H = SVG_H - PAD_T - 28

def field_to_px(x, y):
    return (PAD_L + (x / FIELD_W) * DRAW_W,
            PAD_T + (y / FIELD_H) * DRAW_H)

def build_field_svg(frame_dets, heatmap_pid=None, heatmap_team=None,
                    heatmap_data=None, show_dots=True):
    lines = []
    lines.append(f'<svg width="{SVG_W}" height="{SVG_H}" '
                 f'xmlns="http://www.w3.org/2000/svg" '
                 f'style="background:#2d6a1f;border-radius:8px;width:100%">')

    def ln(x1, y1, x2, y2):
        p1 = field_to_px(x1, y1); p2 = field_to_px(x2, y2)
        lines.append(f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" '
                     f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
                     f'stroke="rgba(255,255,255,0.55)" stroke-width="1.5"/>')

    tl = field_to_px(0, 0); br = field_to_px(FIELD_W, FIELD_H)
    lines.append(f'<rect x="{tl[0]}" y="{tl[1]}" '
                 f'width="{br[0]-tl[0]}" height="{br[1]-tl[1]}" '
                 f'fill="none" stroke="rgba(255,255,255,0.65)" stroke-width="2"/>')
    ln(FIELD_W/2, 0, FIELD_W/2, FIELD_H)
    cc = field_to_px(FIELD_W/2, FIELD_H/2)
    rx = 4.5/FIELD_W*DRAW_W; ry = 4.5/FIELD_H*DRAW_H
    lines.append(f'<ellipse cx="{cc[0]:.1f}" cy="{cc[1]:.1f}" '
                 f'rx="{rx:.1f}" ry="{ry:.1f}" '
                 f'fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="1.5"/>')
    lines.append(f'<circle cx="{cc[0]:.1f}" cy="{cc[1]:.1f}" r="3" '
                 f'fill="rgba(255,255,255,0.55)"/>')
    for side in [0, FIELD_W]:
        s = 1 if side == 0 else -1
        x2 = side + s*10; y1 = FIELD_H/2-6; y2 = FIELD_H/2+6
        ln(side, y1, x2, y1); ln(x2, y1, x2, y2); ln(x2, y2, side, y2)

    if heatmap_data is not None and len(heatmap_data) > 0:
        gw, gh = 25, 15
        grid = np.zeros((gh, gw))
        for (x, y) in heatmap_data:
            gx = min(int(x / FIELD_W * gw), gw-1)
            gy = min(int(y / FIELD_H * gh), gh-1)
            grid[gy, gx] += 1
        mx = grid.max() or 1
        cw = DRAW_W / gw; ch = DRAW_H / gh
        for gy in range(gh):
            for gx in range(gw):
                v = grid[gy, gx] / mx
                if v < 0.05: continue
                px_x = PAD_L + gx * cw; px_y = PAD_T + gy * ch
                if heatmap_team == 0:   color = f"rgba(232,89,60,{v*0.65:.2f})"
                elif heatmap_team == 1: color = f"rgba(59,139,212,{v*0.65:.2f})"
                else:                   color = f"rgba(255,220,80,{v*0.65:.2f})"
                lines.append(f'<rect x="{px_x:.1f}" y="{px_y:.1f}" '
                             f'width="{cw:.1f}" height="{ch:.1f}" '
                             f'fill="{color}" rx="2"/>')

    if show_dots and frame_dets and isinstance(frame_dets, list):
        for det in frame_dets:
            x    = det.get("x_campo", det.get("x", 0))
            y    = det.get("y_campo", det.get("y", 0))
            pid  = det.get("id", det.get("pid", -1))
            team = det.get("equipo", det.get("team", -1))
            ppx, ppy = field_to_px(x, y)
            color = TEAM_COLORS.get(team, "#888")
            sel = (heatmap_pid is not None and pid == heatmap_pid)
            r = 10 if sel else 7
            sw = 2.5 if sel else 1.5
            stroke = "white" if sel else "rgba(0,0,0,0.4)"
            lines.append(f'<circle cx="{ppx:.1f}" cy="{ppy:.1f}" r="{r}" '
                         f'fill="{color}" stroke="{stroke}" stroke-width="{sw}"/>')
            lines.append(f'<text x="{ppx:.1f}" y="{ppy+4:.1f}" '
                         f'text-anchor="middle" font-size="8" '
                         f'font-family="sans-serif" font-weight="bold" '
                         f'fill="white">{pid}</text>')

    lines.append('</svg>')
    return "\n".join(lines)

# ── UI ─────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stSidebar"] { background: #1a1d27; }
h1,h2,h3 { color: #f0f0f0 !important; }
.metric-card {
    background: #1e2130; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 8px;
    border-left: 4px solid var(--c);
}
.metric-card .label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
.metric-card .value { font-size: 24px; font-weight: 700; color: #f0f0f0; margin-top: 2px; }
.metric-card .sub   { font-size: 12px; color: #666; margin-top: 2px; }
.panel-label { font-size: 11px; color: #666; text-transform: uppercase;
               letter-spacing: .6px; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ Análisis táctico 7×7")

with st.sidebar:
    st.header("Cargar datos")
    uploaded = st.file_uploader("partido.zip", type="zip",
        help="ZIP con posiciones_limpias.json + carpeta frames/")
    st.markdown("---")
    st.caption("Genera este archivo con la celda de exportación del Colab.")

if not uploaded:
    st.info("👈 Sube el archivo `partido.zip` desde el panel lateral para comenzar.")
    st.stop()

with st.spinner("Cargando datos..."):
    frames, frame_images = load_zip(uploaded)

if frames is None:
    st.error("No se encontró posiciones_limpias.json dentro del ZIP.")
    st.stop()

n_frames     = len(frames)
trajs        = build_trajectories(frames)
player_team  = {pid: majority_team(pts) for pid, pts in trajs.items()}
players_by_team = defaultdict(list)
for pid, team in player_team.items():
    players_by_team[team].append(pid)
distances    = distance_per_player(trajs)
has_frames   = len(frame_images) > 0

# nearest available frame image
sorted_img_keys = sorted(frame_images.keys()) if has_frames else []

def nearest_frame_image(idx):
    if not sorted_img_keys: return None
    closest = min(sorted_img_keys, key=lambda k: abs(k - idx))
    return frame_images[closest]

# ── Tabs ───────────────────────────────────────────────────────────────────────

tab_campo, tab_dist, tab_heat = st.tabs(["🟢 Campo en vivo", "📏 Distancias", "🌡️ Heatmaps"])

# ── TAB CAMPO ──────────────────────────────────────────────────────────────────
with tab_campo:
    frame_idx = st.slider("Frame", 0, n_frames - 1, 0, key="frame_slider")

    col2d, colv = st.columns(2)

    with col2d:
        st.markdown('<div class="panel-label">Plano 2D</div>', unsafe_allow_html=True)
        svg = build_field_svg(frames[frame_idx])
        st.markdown(svg, unsafe_allow_html=True)

    with colv:
        st.markdown('<div class="panel-label">Video original</div>', unsafe_allow_html=True)
        if has_frames:
            img = nearest_frame_image(frame_idx)
            st.image(img, use_container_width=True)
            if len(sorted_img_keys) > 1:
                step = sorted_img_keys[1] - sorted_img_keys[0]
                st.caption(f"Frame {frame_idx} (exportado cada {step} frames)")
        else:
            st.info("El ZIP no contiene frames de video.\n\n"
                    "Añade la carpeta `frames/` al ZIP con la celda de exportación del Colab.")

    # info jugadores
    st.markdown("---")
    frame_dets = frames[frame_idx]
    by_team = defaultdict(list)
    for d in frame_dets:
        t = d.get("equipo", d.get("team", -1))
        p = d.get("id", d.get("pid", "?"))
        by_team[t].append(p)

    cols = st.columns(len(by_team) or 1)
    for col, team_id in zip(cols, sorted(by_team.keys())):
        with col:
            color = TEAM_COLORS.get(team_id, "#888")
            name  = TEAM_NAMES.get(team_id, f"Equipo {team_id}")
            pids  = sorted(by_team[team_id])
            st.markdown(
                f'<div style="background:#1e2130;border-radius:8px;padding:10px 14px">'
                f'<span style="color:{color};font-weight:600;font-size:13px">{name}</span><br>'
                f'<span style="color:#aaa;font-size:12px">Jugadores: {", ".join(str(p) for p in pids)}</span>'
                f'</div>', unsafe_allow_html=True)

# ── TAB DISTANCIAS ─────────────────────────────────────────────────────────────
with tab_dist:
    st.subheader("Distancia recorrida por jugador")
    st.caption("En metros — escala 1 unidad = 1 m (FIELD_W=50, FIELD_H=30)")

    col1, col2 = st.columns(2)
    for col, team_id in zip([col1, col2], [0, 1]):
        with col:
            color = TEAM_COLORS[team_id]
            name  = TEAM_NAMES[team_id]
            st.markdown(f'<h3 style="color:{color}">{name}</h3>', unsafe_allow_html=True)
            pids = sorted(players_by_team[team_id],
                          key=lambda p: distances.get(p, 0), reverse=True)
            if not pids:
                st.caption("Sin jugadores detectados")
                continue
            max_d = distances.get(pids[0], 1) or 1
            for pid in pids:
                d = distances.get(pid, 0)
                pct = d / max_d * 100
                st.markdown(
                    f'<div style="margin-bottom:10px">'
                    f'<div style="display:flex;justify-content:space-between;font-size:13px;color:#aaa;margin-bottom:3px">'
                    f'<span>Jugador {pid}</span>'
                    f'<span style="font-weight:600;color:#f0f0f0">{d} m</span></div>'
                    f'<div style="background:#2a2d3e;border-radius:4px;height:7px">'
                    f'<div style="background:{color};width:{pct:.1f}%;height:7px;border-radius:4px"></div>'
                    f'</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    for col, team_id in zip([c1, c2], [0, 1]):
        with col:
            total = sum(distances.get(p, 0) for p in players_by_team[team_id])
            color = TEAM_COLORS[team_id]
            name  = TEAM_NAMES[team_id]
            st.markdown(
                f'<div class="metric-card" style="--c:{color}">'
                f'<div class="label">Total {name}</div>'
                f'<div class="value">{total:.0f} m</div>'
                f'<div class="sub">{len(players_by_team[team_id])} jugadores</div>'
                f'</div>', unsafe_allow_html=True)

# ── TAB HEATMAPS ───────────────────────────────────────────────────────────────
with tab_heat:
    st.subheader("Heatmap de posiciones")

    mode = st.radio("Ver heatmap de:", ["Por equipo", "Por jugador"], horizontal=True)

    if mode == "Por equipo":
        col1, col2 = st.columns(2)
        for col, team_id in zip([col1, col2], [0, 1]):
            with col:
                color = TEAM_COLORS[team_id]
                name  = TEAM_NAMES[team_id]
                st.markdown(f'<h4 style="color:{color}">{name}</h4>', unsafe_allow_html=True)
                pts = [(p[1], p[2]) for pid in players_by_team[team_id] for p in trajs[pid]]
                svg = build_field_svg([], heatmap_team=team_id,
                                      heatmap_data=pts, show_dots=False)
                st.markdown(svg, unsafe_allow_html=True)
    else:
        all_pids = sorted(trajs.keys())
        pid_labels = {
            pid: f"Jugador {pid} ({TEAM_NAMES.get(player_team.get(pid,-1), '?')})"
            for pid in all_pids
        }
        selected_pid = st.selectbox(
            "Selecciona jugador",
            options=all_pids,
            format_func=lambda p: pid_labels[p]
        )
        team_id = player_team.get(selected_pid, -1)
        color   = TEAM_COLORS.get(team_id, "#888")
        pts     = [(p[1], p[2]) for p in trajs[selected_pid]]

        col_svg, col_stats = st.columns([3, 1])
        with col_svg:
            svg = build_field_svg(
                frames[st.session_state.get("frame_slider", 0)],
                heatmap_pid=selected_pid,
                heatmap_team=team_id,
                heatmap_data=pts,
                show_dots=True
            )
            st.markdown(svg, unsafe_allow_html=True)

        with col_stats:
            d           = distances.get(selected_pid, 0)
            appearances = len(trajs[selected_pid])
            st.markdown(
                f'<div class="metric-card" style="--c:{color};margin-top:20px">'
                f'<div class="label">Distancia</div>'
                f'<div class="value">{d} m</div></div>'
                f'<div class="metric-card" style="--c:{color}">'
                f'<div class="label">Frames detectado</div>'
                f'<div class="value">{appearances}</div>'
                f'<div class="sub">de {n_frames} totales</div></div>'
                f'<div class="metric-card" style="--c:{color}">'
                f'<div class="label">Equipo</div>'
                f'<div class="value" style="font-size:15px">{TEAM_NAMES.get(team_id,"?")}</div>'
                f'</div>', unsafe_allow_html=True)
