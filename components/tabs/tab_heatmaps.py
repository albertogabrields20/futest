import streamlit as st
from ..field import build_field_svg, TEAM_COLORS, TEAM_NAMES
from ..loaders import get_jugadores, get_pos, get_team

EMPTY_OVS = {k: False for k in [
    "heatmap_equipo","heatmap_diff","voronoi","superioridad",
    "poligono_convexo","rectangulo_bloque","espacio_libre","espacio_lineas",
    "linea_defensiva","linea_presion","lineas_banda","red_proximidad",
    "triangulos","marcajes","radio_presion","centroide","cola","vectores",
]}


def nav_controls(key, n_frames):
    if key not in st.session_state:
        st.session_state[key] = 0

    col_prev, col_next = st.columns([1, 1])
    with col_prev:
        if st.button("◀ Anterior", key=f"{key}_prev"):
            st.session_state[key] = max(0, st.session_state[key] - 1)
    with col_next:
        if st.button("Siguiente ▶", key=f"{key}_next"):
            st.session_state[key] = min(n_frames - 1, st.session_state[key] + 1)

    def on_slider():
        st.session_state[key] = st.session_state[f"{key}_slider"]

    st.slider("Frame", 0, n_frames - 1,
              value=st.session_state[key],
              key=f"{key}_slider", on_change=on_slider)
    return st.session_state[key]


def render(frames, heatmap_all, heatmap_diff_data):
    n_frames = len(frames)
    st.subheader("Heatmap de posiciones")

    mode = st.radio("Ver:", ["Partido completo", "Frame a frame"], horizontal=True)
    tipo = st.radio("Tipo:", ["Por equipo", "Diferencial E1 vs E2"], horizontal=True)

    if mode == "Frame a frame":
        frame_idx = nav_controls("heat_frame", n_frames)
        st.caption(f"Frame {frame_idx} de {n_frames - 1}")

        jugadores = get_jugadores(frames[frame_idx])
        pts_frame = {0: [], 1: []}
        for det in jugadores:
            if not isinstance(det, dict): continue
            t = get_team(det)
            if t in pts_frame:
                pts_frame[t].append(get_pos(det))

        if tipo == "Por equipo":
            col1, col2 = st.columns(2)
            for col, team_id in zip([col1, col2], [0, 1]):
                with col:
                    color = TEAM_COLORS[team_id]
                    st.markdown(f'<h4 style="color:{color}">{TEAM_NAMES[team_id]}</h4>',
                                unsafe_allow_html=True)
                    ovs = {**EMPTY_OVS, "heatmap_equipo": True}
                    st.markdown(build_field_svg(
                        jugadores, ovs,
                        heatmap_data=pts_frame[team_id],
                        heatmap_team=team_id,
                    ), unsafe_allow_html=True)
        else:
            st.caption("Rojo = domina E1 · Azul = domina E2")
            ovs = {**EMPTY_OVS, "heatmap_diff": True}
            st.markdown(build_field_svg(
                jugadores, ovs,
                heatmap_diff={"e0": pts_frame[0], "e1": pts_frame[1]},
            ), unsafe_allow_html=True)

    else:  # Partido completo
        if tipo == "Por equipo":
            col1, col2 = st.columns(2)
            for col, team_id in zip([col1, col2], [0, 1]):
                with col:
                    color = TEAM_COLORS[team_id]
                    st.markdown(f'<h4 style="color:{color}">{TEAM_NAMES[team_id]}</h4>',
                                unsafe_allow_html=True)
                    ovs = {**EMPTY_OVS, "heatmap_equipo": True}
                    st.markdown(build_field_svg(
                        [], ovs,
                        heatmap_data=heatmap_all[team_id],
                        heatmap_team=team_id,
                    ), unsafe_allow_html=True)
        else:
            st.caption("Rojo = domina E1 · Azul = domina E2")
            ovs = {**EMPTY_OVS, "heatmap_diff": True}
            st.markdown(build_field_svg(
                [], ovs, heatmap_diff=heatmap_diff_data,
            ), unsafe_allow_html=True)
