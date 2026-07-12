import streamlit as st
import streamlit.components.v1 as components
from ..loaders import get_jugadores, get_pid, get_team
from ..field import build_field_svg, TEAM_COLORS, TEAM_NAMES


def render(frames, frame_images, trajs, heatmap_all, heatmap_diff_data,
           ovs, sorted_img_keys):

    n_frames = len(frames)

    # ── Rango de reproducción ─────────────────────────────────
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

    # ── Slider + botones con JS para reproducción ─────────────
    # El JS controla el slider nativo de Streamlit directamente
    speed_ms = st.select_slider(
        "Velocidad", options=[50, 100, 200, 400],
        value=100, format_func=lambda x: f"{x}ms/frame", key="speed"
    )

    components.html(f"""
    <div style="display:flex;gap:10px;margin:4px 0">
      <button id="btn-play" onclick="startPlay()" style="
        background:#1e2130;border:1px solid #1D9E75;color:#1D9E75;
        padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px">
        ▶ Reproducir
      </button>
      <button id="btn-stop" onclick="stopPlay()" style="
        background:#1e2130;border:1px solid #3a3d50;color:#aaa;
        padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px">
        ⏹ Detener
      </button>
      <span id="status" style="color:#666;font-size:12px;align-self:center">
        Listo
      </span>
    </div>
    <script>
      let interval = null;
      const START = {start_frame};
      const END   = {end_frame};
      const SPEED = {speed_ms};

      function getSlider() {{
        // Streamlit slider input
        return parent.document.querySelectorAll('input[type="range"]')[0];
      }}

      function setFrame(val) {{
        const slider = getSlider();
        if (!slider) return;
        const nativeInput = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype, 'value'
        );
        nativeInput.set.call(slider, val);
        slider.dispatchEvent(new Event('input', {{ bubbles: true }}));
        slider.dispatchEvent(new Event('change', {{ bubbles: true }}));
      }}

      function startPlay() {{
        if (interval) clearInterval(interval);
        document.getElementById('status').textContent = '▶ Reproduciendo';
        document.getElementById('btn-play').style.borderColor = '#1D9E75';
        const slider = getSlider();
        let cur = slider ? parseInt(slider.value) : START;
        if (cur >= END) cur = START;
        interval = setInterval(() => {{
          if (cur > END) {{
            stopPlay();
            return;
          }}
          setFrame(cur);
          cur++;
        }}, SPEED);
      }}

      function stopPlay() {{
        if (interval) clearInterval(interval);
        interval = null;
        document.getElementById('status').textContent = '⏸ Detenido';
        document.getElementById('btn-play').style.borderColor = '#3a3d50';
      }}
    </script>
    """, height=60)

    # ── Slider principal ──────────────────────────────────────
    frame_idx = st.slider(
        "Frame",
        min_value=start_frame,
        max_value=end_frame,
        value=start_frame,
        key="frame_slider_display"
    )

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
                st.caption(f"Frame {frame_idx} · exportado cada {step} frames")
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
