import streamlit as st
from ..loaders import get_jugadores, get_pid, get_team
from ..field import build_field_svg, TEAM_COLORS, TEAM_NAMES


def render(frames, frame_images, trajs, heatmap_all, heatmap_diff_data,
           ovs, sorted_img_keys):

    n_frames = len(frames)

    # ── Inicializar frame actual ──────────────────────────────
    if "current_frame" not in st.session_state:
        st.session_state["current_frame"] = 0

    # ── Rango de navegación ───────────────────────────────────
    col_s, col_e = st.columns(2)
    with col_s:
        start_frame = int(st.number_input(
            "Frame inicio", 0, n_frames-1, 0, step=1, key="start_frame"
        ))
    with col_e:
        end_frame = int(st.number_input(
            "Frame fin", 0, n_frames-1, n_frames-1, step=1, key="end_frame"
        ))

    if start_frame > end_frame:
        st.warning("El frame de inicio debe ser menor que el de fin.")
        start_frame, end_frame = 0, n_frames - 1

    # ── Slider ────────────────────────────────────────────────
    frame_idx = st.slider(
        "Frame",
        min_value=start_frame,
        max_value=end_frame,
        value=int(st.session_state["current_frame"]),
        key="frame_slider_display"
    )
    st.session_state["current_frame"] = frame_idx

    # ── Botones anterior / siguiente ──────────────────────────
    col_prev, col_next, col_info = st.columns([1, 1, 4])
    with col_prev:
        if st.button("◀ Anterior", key="btn_prev"):
            new = max(start_frame, frame_idx - 1)
            st.session_state["current_frame"] = new
            st.rerun()
    with col_next:
        if st.button("Siguiente ▶", key="btn_next"):
            new = min(end_frame, frame_idx + 1)
            st.session_state["current_frame"] = new
            st.rerun()
    with col_info:
        st.caption(f"Frame {frame_idx} de {n_frames-1}")

    # ── Plano 2D + Video ──────────────────────────────────────
    jugadores_frame = get_jugadores(frames[frame_idx])
    heat_team_id = 0 if st.session_state.get("heat_team") == "E1" else 1
    heat_data = heatmap_all[heat_team_id] if ovs.get("heatmap_equipo") else None

    col2d, colv = st.columns(2)
    with col2d:
        st.markdown('<div class="panel-label">Plano 2D</div>', unsafe_allow_html=True)
        st.markdown(build_field_svg(
            jugadores_frame, ovs,
            trajs=trajs,
            frame_idx=frame_idx,
            heatmap_data=heat_data,
            heatmap_team=heat_team_id,
            heatmap_diff=heatmap_diff_data if ovs.get("heatmap_diff") else None,
            frames_data=frames,
        ), unsafe_allow_html=True)

    with colv:
        st.markdown('<div class="panel-label">Vídeo original</div>', unsafe_allow_html=True)
        if sorted_img_keys:
            closest = min(sorted_img_keys, key=lambda k: abs(k - frame_idx))
            st.image(frame_images[closest])
            if len(sorted_img_keys) > 1:
                step = sorted_img_keys[1] - sorted_img_keys[0]
                st.caption(f"Frame exportado cada {step} frames")
        else:
            st.info("El ZIP no contiene frames de vídeo.")

    # ── Info jugadores ────────────────────────────────────────
    st.markdown("---")
    by_team = {}
    for det in jugadores_frame:
        if not isinstance(det, dict): continue
        t = get_team(det)
        by_team.setdefault(t, []).append(get_pid(det))

    cols = st.columns(max(len(by_team), 1))
    for col, team_id in zip(cols, sorted(by_team.keys())):
        with col:
            color = TEAM_COLORS.get(team_id, "#888")
            n = len(by_team[team_id])
            st.markdown(
                f'<div style="background:#1e2130;border-radius:8px;padding:10px 14px">'
                f'<span style="color:{color};font-weight:600;font-size:13px">'
                f'{TEAM_NAMES.get(team_id,"?")}</span><br>'
                f'<span style="color:#aaa;font-size:12px">'
                f'{n} detecciones en este frame</span>'
                f'</div>', unsafe_allow_html=True)
