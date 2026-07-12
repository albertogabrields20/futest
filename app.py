import streamlit as st
from components.loaders import load_zip
from components.stats import (
    build_trajectories, build_player_team_map,
    build_players_by_team, distance_per_player, precompute_heatmaps,
)
from components.tabs import tab_campo, tab_heatmaps, tab_metricas

st.set_page_config(
    page_title="Análisis táctico 7x7",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stSidebar"]          { background: #1a1d27; }
h1,h2,h3 { color: #f0f0f0 !important; }
.metric-card {
    background: #1e2130; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 8px;
    border-left: 4px solid var(--c);
}
.metric-card .label { font-size:11px; color:#888; text-transform:uppercase; letter-spacing:1px; }
.metric-card .value { font-size:24px; font-weight:700; color:#f0f0f0; margin-top:2px; }
.metric-card .sub   { font-size:12px; color:#666; margin-top:2px; }
.panel-label        { font-size:11px; color:#666; text-transform:uppercase;
                      letter-spacing:.6px; margin-bottom:6px; }
.ov-section         { font-size:11px; font-weight:500; color:#888;
                      text-transform:uppercase; letter-spacing:.5px; margin:12px 0 4px; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ Análisis táctico 7×7")

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.header("Cargar datos")
    uploaded = st.file_uploader("partido.zip", type="zip")
    st.markdown("---")

    st.markdown("### Overlays del campo 2D")

    st.markdown('<div class="ov-section">Colectivos</div>', unsafe_allow_html=True)
    ov_poligono  = st.checkbox("Polígono convexo",      value=True)
    ov_bloque    = st.checkbox("Rectángulo de bloque",  value=False)
    ov_centroide = st.checkbox("Centroide del equipo",  value=True)

    st.markdown('<div class="ov-section">Líneas de bloque</div>', unsafe_allow_html=True)
    ov_linea_def   = st.checkbox("Línea defensiva",      value=True)
    ov_linea_pre   = st.checkbox("Línea de presión",     value=False)
    ov_espacio_lin = st.checkbox("Espacio entre líneas", value=False)
    ov_bandas      = st.checkbox("Líneas de banda",      value=False)

    st.markdown('<div class="ov-section">Relaciones</div>', unsafe_allow_html=True)
    ov_red        = st.checkbox("Red de proximidad",     value=False)
    ov_triangulos = st.checkbox("Triángulos de juego",   value=False)
    ov_marcajes   = st.checkbox("Marcajes más cercanos", value=False)
    ov_radio      = st.checkbox("Radio de presión",      value=False)

    st.markdown('<div class="ov-section">Espacio</div>', unsafe_allow_html=True)
    ov_voronoi = st.checkbox("Zonas Voronoi",         value=False)
    ov_superio = st.checkbox("Superioridad por zona", value=False)
    ov_libre   = st.checkbox("Espacio libre",         value=False)

    st.markdown('<div class="ov-section">Heatmaps</div>', unsafe_allow_html=True)
    ov_heat_eq   = st.checkbox("Heatmap por equipo",  value=False)
    ov_heat_team = st.radio("Equipo heatmap", ["E1", "E2"], horizontal=True,
                            label_visibility="collapsed", key="heat_team")
    ov_heat_diff = st.checkbox("Heatmap diferencial", value=False)

    st.markdown('<div class="ov-section">Movimiento</div>', unsafe_allow_html=True)
    ov_cola     = st.checkbox("Cola de trayectoria",   value=False)
    ov_vectores = st.checkbox("Vectores de velocidad", value=False)

    st.caption("Genera partido.zip desde el Colab.")

ovs = {
    "poligono_convexo":  ov_poligono,
    "rectangulo_bloque": ov_bloque,
    "centroide":         ov_centroide,
    "linea_defensiva":   ov_linea_def,
    "linea_presion":     ov_linea_pre,
    "espacio_lineas":    ov_espacio_lin,
    "lineas_banda":      ov_bandas,
    "red_proximidad":    ov_red,
    "triangulos":        ov_triangulos,
    "marcajes":          ov_marcajes,
    "radio_presion":     ov_radio,
    "voronoi":           ov_voronoi,
    "superioridad":      ov_superio,
    "espacio_libre":     ov_libre,
    "heatmap_equipo":    ov_heat_eq,
    "heatmap_diff":      ov_heat_diff,
    "cola":              ov_cola,
    "vectores":          ov_vectores,
}

if not uploaded:
    st.info("👈 Sube el archivo `partido.zip` para comenzar.")
    st.stop()

# ── Cargar datos ──────────────────────────────────────────────
with st.spinner("Cargando datos..."):
    frames, frame_images, _ = load_zip(uploaded)

if not frames:
    st.error("No se encontró posiciones_limpias.json dentro del ZIP.")
    st.stop()

trajs           = build_trajectories(frames)
player_team     = build_player_team_map(trajs)
players_by_team = build_players_by_team(player_team)
distances       = distance_per_player(trajs)
heatmap_all, heatmap_diff_data = precompute_heatmaps(trajs, player_team)
sorted_img_keys = sorted(frame_images.keys()) if frame_images else []

# ── Tabs ──────────────────────────────────────────────────────
t_campo, t_heat, t_metricas = st.tabs([
    "🟢 Campo en vivo",
    "🌡️ Heatmaps",
    "📊 Métricas tácticas",
])

with t_campo:
    tab_campo.render(frames, frame_images, trajs,
                     heatmap_all, heatmap_diff_data,
                     ovs, sorted_img_keys)

with t_heat:
    tab_heatmaps.render(heatmap_all, heatmap_diff_data)

with t_metricas:
    tab_metricas.render(frames, player_team)
