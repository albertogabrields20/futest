import streamlit as st
from ..field import build_field_svg, TEAM_COLORS, TEAM_NAMES


def render(heatmap_all, heatmap_diff_data):
    st.subheader("Heatmap de posiciones")
    mode = st.radio("Ver:", ["Por equipo", "Diferencial E1 vs E2"], horizontal=True)

    empty_ovs = {
        "heatmap_equipo": False, "heatmap_diff": False,
        "voronoi": False, "superioridad": False, "poligono_convexo": False,
        "rectangulo_bloque": False, "espacio_libre": False, "espacio_lineas": False,
        "linea_defensiva": False, "linea_presion": False, "lineas_banda": False,
        "red_proximidad": False, "triangulos": False, "marcajes": False,
        "radio_presion": False, "centroide": False, "cola": False, "vectores": False,
    }

    if mode == "Por equipo":
        col1, col2 = st.columns(2)
        for col, team_id in zip([col1, col2], [0, 1]):
            with col:
                color = TEAM_COLORS[team_id]
                st.markdown(f'<h4 style="color:{color}">{TEAM_NAMES[team_id]}</h4>',
                            unsafe_allow_html=True)
                ovs = {**empty_ovs, "heatmap_equipo": True}
                st.markdown(build_field_svg([], ovs,
                    heatmap_data=heatmap_all[team_id],
                    heatmap_team=team_id), unsafe_allow_html=True)
    else:
        st.caption("Rojo = domina E1 · Azul = domina E2 · Sin color = equilibrado")
        ovs = {**empty_ovs, "heatmap_diff": True}
        st.markdown(build_field_svg([], ovs,
            heatmap_diff=heatmap_diff_data), unsafe_allow_html=True)
