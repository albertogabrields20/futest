import streamlit as st
from ..field import TEAM_COLORS, TEAM_NAMES, FIELD_W


def render(metricas):
    if not metricas:
        st.info(
            "El ZIP no contiene `metricas.json` — "
            "ejecuta la Celda 5.D en Colab y regenera el export."
        )
        return

    try:
        import pandas as pd
        import plotly.graph_objects as go
    except ImportError:
        st.error("Instala plotly y pandas en requirements.txt")
        return

    m = metricas
    res = m["resumen"]

    st.subheader("Resumen del partido")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Posesión territorial E1",
                        f"{res['posesion_territorial_pct']['e0']}%")
    with c2: st.metric("Posesión territorial E2",
                        f"{res['posesion_territorial_pct']['e1']}%")
    with c3: st.metric("Presión media", f"{res['presion_media_m']}m",
                        help="Distancia media entre equipos.")
    with c4: st.metric("Duración analizada", f"{res['duracion_s']}s")

    st.markdown("---")
    col1, col2 = st.columns(2)
    for col, eq_key, eq_id in [(col1, "e0", 0), (col2, "e1", 1)]:
        with col:
            color = TEAM_COLORS[eq_id]
            st.markdown(f'<h3 style="color:{color}">{TEAM_NAMES[eq_id]}</h3>',
                        unsafe_allow_html=True)
            cards = [
                ("Distancia total", f"{res['distancia_total_m'][eq_key]:.0f} m", ""),
                ("Vel. máxima",
                 f"{res['velocidad_maxima_ms'][eq_key]} m/s",
                 f"{res['velocidad_maxima_ms'][eq_key]*3.6:.1f} km/h"),
                ("Vel. media", f"{res['velocidad_media_ms'][eq_key]} m/s", ""),
                ("Compacidad media",
                 f"{res['compacidad_media_m'][eq_key]} m",
                 "profundidad del bloque"),
                ("Posición media",
                 f"{res['posicion_media_x'][eq_key]} m",
                 "0=portería izq · 50=portería der"),
            ]
            for label, value, sub in cards:
                st.markdown(
                    f'<div class="metric-card" style="--c:{color}">'
                    f'<div class="label">{label}</div>'
                    f'<div class="value">{value}</div>'
                    + (f'<div class="sub">{sub}</div>' if sub else '') +
                    f'</div>', unsafe_allow_html=True)

            zonas = res.get("distribucion_zonas_pct", {}).get(eq_key, {})
            if zonas:
                badges = "".join(
                    f'<span style="background:{color}22;color:{color};'
                    f'padding:3px 10px;border-radius:12px;font-size:12px;'
                    f'margin-right:4px">{z.capitalize()} {pct}%</span>'
                    for z, pct in zonas.items()
                )
                st.markdown(
                    f'<div class="metric-card" style="--c:{color}">'
                    f'<div class="label">Distribución por zonas</div>'
                    f'<div style="margin-top:8px">{badges}</div>'
                    f'</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Evolución temporal")
    frames_m = m.get("por_frame", [])
    if not frames_m:
        st.info("No hay datos temporales en metricas.json")
        return

    df = pd.DataFrame([{
        "tiempo":   f["tiempo"],
        "cx_e0":    f["e0"]["centroide_x"],
        "cx_e1":    f["e1"]["centroide_x"],
        "comp_e0":  f["e0"]["profundidad"],
        "comp_e1":  f["e1"]["profundidad"],
        "presion":  f["distancia_entre_equipos"],
    } for f in frames_m
        if f["e0"]["centroide_x"] is not None
        and f["e1"]["centroide_x"] is not None])

    layout_base = dict(
        paper_bgcolor="#0f1117", plot_bgcolor="#1e2130",
        font_color="#f0f0f0",
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(bgcolor="#1e2130"),
    )

    tab_c, tab_co, tab_p = st.tabs(["Posición en campo", "Compacidad", "Presión"])

    with tab_c:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["tiempo"], y=df["cx_e0"],
                                 name="E1", line=dict(color="#E8593C")))
        fig.add_trace(go.Scatter(x=df["tiempo"], y=df["cx_e1"],
                                 name="E2", line=dict(color="#3B8BD4")))
        fig.add_hline(y=FIELD_W/2, line_dash="dash",
                      line_color="white", opacity=0.2)
        fig.update_layout(**layout_base,
                          xaxis_title="Tiempo (s)", yaxis_title="X (m)",
                          yaxis=dict(range=[0, FIELD_W]))
        st.plotly_chart(fig, use_container_width=True)

    with tab_co:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df["tiempo"], y=df["comp_e0"],
                                  name="E1", line=dict(color="#E8593C")))
        fig2.add_trace(go.Scatter(x=df["tiempo"], y=df["comp_e1"],
                                  name="E2", line=dict(color="#3B8BD4")))
        fig2.update_layout(**layout_base,
                           xaxis_title="Tiempo (s)", yaxis_title="Profundidad (m)")
        st.plotly_chart(fig2, use_container_width=True)

    with tab_p:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=df["tiempo"], y=df["presion"],
                                  name="Presión", line=dict(color="#facc15")))
        fig3.update_layout(**layout_base,
                           xaxis_title="Tiempo (s)",
                           yaxis_title="Distancia entre equipos (m)")
        st.plotly_chart(fig3, use_container_width=True)
