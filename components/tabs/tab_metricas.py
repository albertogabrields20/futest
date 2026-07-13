import streamlit as st
import math
from collections import defaultdict
from ..loaders import get_jugadores, get_pos, get_team, get_pid
from ..field import TEAM_COLORS, TEAM_NAMES, FIELD_W


def calcular_metricas(frames, player_team):
    resumen = {
        "distancia_total_m":       {"e0": 0.0, "e1": 0.0},
        "velocidad_maxima_ms":     {"e0": 0.0, "e1": 0.0},
        "velocidad_media_ms":      {"e0": 0.0, "e1": 0.0},
        "compacidad_media_m":      {"e0": 0.0, "e1": 0.0},
        "posicion_media_x":        {"e0": 0.0, "e1": 0.0},
        "posesion_territorial_pct":{"e0": 0,   "e1": 0},
        "presion_media_m":         0.0,
        "duracion_s":              0.0,
        "distribucion_zonas_pct":  {"e0": {}, "e1": {}},
    }

    por_frame = []
    prev_pos = {}
    vel_sums = {"e0": 0.0, "e1": 0.0}
    vel_counts = {"e0": 0, "e1": 0}
    pos_sums = {"e0": 0.0, "e1": 0.0}
    pos_counts = {"e0": 0, "e1": 0}
    compact_sums = {"e0": 0.0, "e1": 0.0}
    compact_counts = {"e0": 0, "e1": 0}
    presion_sum = 0.0
    presion_count = 0
    territorial_e0 = 0
    territorial_e1 = 0
    zona_counts = {"e0": {"defensa":0,"medio":0,"ataque":0},
                   "e1": {"defensa":0,"medio":0,"ataque":0}}

    for frame in frames:
        jugs = get_jugadores(frame)
        tiempo = frame.get("tiempo_s", 0) if isinstance(frame, dict) else 0
        pts = {0: [], 1: []}

        for det in jugs:
            if not isinstance(det, dict): continue
            pid = get_pid(det)
            x, y = get_pos(det)
            team = get_team(det)
            eq_key = "e0" if team == 0 else "e1" if team == 1 else None

            if eq_key:
                pts[team].append((x, y))
                pos_sums[eq_key] += x
                pos_counts[eq_key] += 1
                # Zonas
                if x < FIELD_W/3:       zona_counts[eq_key]["defensa"] += 1
                elif x < 2*FIELD_W/3:   zona_counts[eq_key]["medio"] += 1
                else:                    zona_counts[eq_key]["ataque"] += 1

            if pid in prev_pos and eq_key:
                dx = x - prev_pos[pid][0]; dy = y - prev_pos[pid][1]
                speed = math.hypot(dx, dy)
                resumen["distancia_total_m"][eq_key] += speed
                resumen["velocidad_maxima_ms"][eq_key] = max(
                    resumen["velocidad_maxima_ms"][eq_key], speed)
                vel_sums[eq_key] += speed
                vel_counts[eq_key] += 1

            prev_pos[pid] = (x, y)

        for team_id, eq_key in [(0, "e0"), (1, "e1")]:
            if len(pts[team_id]) >= 2:
                xs = [p[0] for p in pts[team_id]]
                compact_sums[eq_key] += max(xs) - min(xs)
                compact_counts[eq_key] += 1

        c0 = sum(p[0] for p in pts[0])/len(pts[0]) if pts[0] else None
        c1 = sum(p[0] for p in pts[1])/len(pts[1]) if pts[1] else None

        if c0 is not None and c1 is not None:
            if c0 > c1: territorial_e0 += 1
            else:        territorial_e1 += 1
            presion = abs(c0 - c1)
            presion_sum += presion
            presion_count += 1
        else:
            presion = None

        por_frame.append({
            "tiempo":  round(tiempo, 2),
            "e0":      {"centroide_x": round(c0, 2) if c0 else None,
                        "profundidad": round(compact_sums["e0"]/max(compact_counts["e0"],1), 2)},
            "e1":      {"centroide_x": round(c1, 2) if c1 else None,
                        "profundidad": round(compact_sums["e1"]/max(compact_counts["e1"],1), 2)},
            "distancia_entre_equipos": round(presion, 2) if presion else None,
        })

    for eq_key in ["e0", "e1"]:
        resumen["distancia_total_m"][eq_key]    = round(resumen["distancia_total_m"][eq_key], 1)
        resumen["velocidad_maxima_ms"][eq_key]  = round(resumen["velocidad_maxima_ms"][eq_key], 2)
        resumen["velocidad_media_ms"][eq_key]   = round(vel_sums[eq_key]/max(vel_counts[eq_key],1), 2)
        resumen["compacidad_media_m"][eq_key]   = round(compact_sums[eq_key]/max(compact_counts[eq_key],1), 1)
        resumen["posicion_media_x"][eq_key]     = round(pos_sums[eq_key]/max(pos_counts[eq_key],1), 1)
        total_z = sum(zona_counts[eq_key].values()) or 1
        resumen["distribucion_zonas_pct"][eq_key] = {
            z: round(v/total_z*100) for z, v in zona_counts[eq_key].items()
        }

    total_t = territorial_e0 + territorial_e1 or 1
    resumen["posesion_territorial_pct"]["e0"] = round(territorial_e0/total_t*100)
    resumen["posesion_territorial_pct"]["e1"] = round(territorial_e1/total_t*100)
    resumen["presion_media_m"]  = round(presion_sum/max(presion_count,1), 1)
    resumen["duracion_s"]       = round(por_frame[-1]["tiempo"] if por_frame else 0, 1)

    return {"resumen": resumen, "por_frame": por_frame}


def render(frames, player_team):
    st.subheader("Métricas tácticas")
    if not frames:
        st.info("Carga un archivo partido.zip para ver las métricas.")
        return

    try:
        import pandas as pd
        import plotly.graph_objects as go
    except ImportError:
        st.error("Añade plotly y pandas al requirements.txt")
        return

    with st.spinner("Calculando métricas..."):
        m = calcular_metricas(frames, player_team)

    res = m["resumen"]
    por_frame = m.get("por_frame", [])

    tab_resumen, tab_evolucion = st.tabs(["📋 Resumen", "📈 Evolución temporal"])

    # ── Resumen ───────────────────────────────────────────────
    with tab_resumen:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Posesión territorial E1", f"{res['posesion_territorial_pct']['e0']}%")
        with c2: st.metric("Posesión territorial E2", f"{res['posesion_territorial_pct']['e1']}%")
        with c3: st.metric("Presión media", f"{res['presion_media_m']} m",
                            help="Distancia media entre centroides.")
        with c4: st.metric("Duración analizada", f"{res['duracion_s']} s")

        st.markdown("---")
        col1, col2 = st.columns(2)
        for col, eq_key, eq_id in [(col1,"e0",0),(col2,"e1",1)]:
            with col:
                color = TEAM_COLORS[eq_id]
                st.markdown(f'<h3 style="color:{color}">{TEAM_NAMES[eq_id]}</h3>',
                            unsafe_allow_html=True)
                cards = [
                    ("Distancia total",    f"{res['distancia_total_m'][eq_key]} m", ""),
                    ("Velocidad máxima",   f"{res['velocidad_maxima_ms'][eq_key]} m/s",
                     f"{res['velocidad_maxima_ms'][eq_key]*3.6:.1f} km/h"),
                    ("Velocidad media",    f"{res['velocidad_media_ms'][eq_key]} m/s", ""),
                    ("Amplitud del bloque",f"{res['compacidad_media_m'][eq_key]} m",
                     "distancia entre jugador más adelantado y más retrasado"),
                    ("Posición media",     f"{res['posicion_media_x'][eq_key]} m",
                     "0=portería izq · 50=portería der"),
                ]
                for label, value, sub in cards:
                    st.markdown(
                        f'<div class="metric-card" style="--c:{color}">'
                        f'<div class="label">{label}</div>'
                        f'<div class="value">{value}</div>'
                        + (f'<div class="sub">{sub}</div>' if sub else '') +
                        f'</div>', unsafe_allow_html=True)

                zonas = res["distribucion_zonas_pct"].get(eq_key, {})
                if zonas:
                    badges = "".join(
                        f'<span style="background:{color}22;color:{color};'
                        f'padding:3px 10px;border-radius:12px;font-size:12px;margin-right:4px">'
                        f'{z.capitalize()} {pct}%</span>'
                        for z, pct in zonas.items()
                    )
                    st.markdown(
                        f'<div class="metric-card" style="--c:{color}">'
                        f'<div class="label">Distribución por zonas</div>'
                        f'<div style="margin-top:8px">{badges}</div>'
                        f'</div>', unsafe_allow_html=True)

    # ── Evolución temporal ────────────────────────────────────
    with tab_evolucion:
        if not por_frame:
            st.info("No hay datos temporales.")
            return

        import pandas as pd
        import plotly.graph_objects as go

        df = pd.DataFrame([{
            "tiempo":  f["tiempo"],
            "cx_e0":   f["e0"]["centroide_x"],
            "cx_e1":   f["e1"]["centroide_x"],
            "comp_e0": f["e0"]["profundidad"],
            "comp_e1": f["e1"]["profundidad"],
            "presion": f.get("distancia_entre_equipos"),
        } for f in por_frame
            if f["e0"]["centroide_x"] is not None
            and f["e1"]["centroide_x"] is not None
        ])

        n_frames = len(frames)
        if "evol_frame" not in st.session_state:
            st.session_state["evol_frame"] = 0

        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("◀ Anterior", key="evol_prev"):
                st.session_state["evol_frame"] = max(0, st.session_state["evol_frame"] - 1)
        with col_next:
            if st.button("Siguiente ▶", key="evol_next"):
                st.session_state["evol_frame"] = min(n_frames - 1, st.session_state["evol_frame"] + 1)

        def on_evol_slider():
            st.session_state["evol_frame"] = st.session_state["evol_slider"]

        frame_idx = st.session_state["evol_frame"]
        st.slider("Frame", 0, n_frames - 1,
                  value=frame_idx,
                  key="evol_slider", on_change=on_evol_slider)

        # Tiempo del frame actual
        t_actual = por_frame[frame_idx]["tiempo"] if frame_idx < len(por_frame) else 0
        st.caption(f"Frame {frame_idx} · Tiempo {t_actual:.1f}s")

        layout_base = dict(
            paper_bgcolor="#0f1117", plot_bgcolor="#1e2130",
            font_color="#f0f0f0",
            margin=dict(l=40, r=20, t=30, b=40),
            legend=dict(bgcolor="#1e2130"),
        )

        def add_vline(fig, t):
            fig.add_vline(x=t, line_color="rgba(255,255,255,0.5)",
                          line_width=1.5, line_dash="dash")

        tab_c, tab_co, tab_p = st.tabs(["Posición en campo", "Amplitud del bloque", "Presión"])

        with tab_c:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["tiempo"], y=df["cx_e0"],
                                     name="E1", line=dict(color="#E8593C")))
            fig.add_trace(go.Scatter(x=df["tiempo"], y=df["cx_e1"],
                                     name="E2", line=dict(color="#3B8BD4")))
            fig.add_hline(y=FIELD_W/2, line_dash="dash", line_color="white", opacity=0.2)
            add_vline(fig, t_actual)
            fig.update_layout(**layout_base, xaxis_title="Tiempo (s)",
                              yaxis_title="Posición X (m)", yaxis=dict(range=[0, FIELD_W]))
            st.plotly_chart(fig, use_container_width=True)

        with tab_co:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df["tiempo"], y=df["comp_e0"],
                                      name="E1", line=dict(color="#E8593C")))
            fig2.add_trace(go.Scatter(x=df["tiempo"], y=df["comp_e1"],
                                      name="E2", line=dict(color="#3B8BD4")))
            add_vline(fig2, t_actual)
            fig2.update_layout(**layout_base, xaxis_title="Tiempo (s)",
                               yaxis_title="Amplitud (m)")
            st.plotly_chart(fig2, use_container_width=True)

        with tab_p:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df["tiempo"], y=df["presion"],
                                      name="Presión", line=dict(color="#facc15")))
            add_vline(fig3, t_actual)
            fig3.update_layout(**layout_base, xaxis_title="Tiempo (s)",
                               yaxis_title="Distancia entre equipos (m)")
            st.plotly_chart(fig3, use_container_width=True)
