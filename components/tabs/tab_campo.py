import streamlit as st
from ..loaders import get_jugadores, get_pid, get_team, get_frame_image
from ..field import build_field_svg, TEAM_COLORS, TEAM_NAMES
from ..nav import nav_controls


def render(frames, frame_index, zip_bytes, trajs, heatmap_all, heatmap_diff_data, ovs):
    n_frames = len(frames)
    frame_idx = nav_controls("campo_frame", n_frames)

    jugadores_frame = get_jugadores(frames[frame_idx])
    heat_team_id = 0 if st.session_state.get("heat_team") == "E1" else 1
    heat_data = heatmap_all[heat_team_id] if ovs.get("heatmap_equipo") else None

    col2d, colv = st.columns(2)
    with col2d:
        st.markdown('<div class="panel-label">Plano 2D</div>', unsafe_allow_html=True)
        st.markdown(build_field_svg(
            jugadores_frame, ovs,
            trajs=trajs, frame_idx=frame_idx,
            heatmap_data=heat_data, heatmap_team=heat_team_id,
            heatmap_diff=heatmap_diff_data if ovs.get("heatmap_diff") else None,
            frames_data=frames,
        ), unsafe_allow_html=True)

    with colv:
        st.markdown('<div class="panel-label">Vídeo original</div>', unsafe_allow_html=True)
        if frame_index:
            img = get_frame_image(zip_bytes, frame_index, frame_idx)
            if img:
                st.image(img)
                if len(frame_index) > 1:
                    keys = sorted(frame_index.keys())
                    step = keys[1] - keys[0] if len(keys) > 1 else 1
                    st.caption(f"Exportado cada {step} frames")
        else:
            st.info("El ZIP no contiene frames de vídeo.")

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
            st.markdown(
                f'<div style="background:#1e2130;border-radius:8px;padding:10px 14px">'
                f'<span style="color:{color};font-weight:600;font-size:13px">'
                f'{TEAM_NAMES.get(team_id,"?")}</span><br>'
                f'<span style="color:#aaa;font-size:12px">'
                f'{len(by_team[team_id])} detecciones en este frame</span>'
                f'</div>', unsafe_allow_html=True)
