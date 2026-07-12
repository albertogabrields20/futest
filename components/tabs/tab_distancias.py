import streamlit as st
from ..field import TEAM_COLORS, TEAM_NAMES


def render(players_by_team, distances):
    st.subheader("Distancia recorrida por equipo")
    st.caption("Métricas a nivel de equipo — el desglose por jugador estará disponible con tracking mejorado.")

    c1, c2 = st.columns(2)
    for col, team_id in zip([c1, c2], [0, 1]):
        with col:
            color = TEAM_COLORS[team_id]
            total = sum(distances.get(p, 0) for p in players_by_team[team_id])
            n = len(players_by_team[team_id])
            promedio = total / n if n > 0 else 0
            st.markdown(
                f'<div class="metric-card" style="--c:{color}">'
                f'<div class="label">Distancia total {TEAM_NAMES[team_id]}</div>'
                f'<div class="value">{total:.0f} m</div>'
                f'<div class="sub">{n} trayectorias detectadas</div>'
                f'</div>'
                f'<div class="metric-card" style="--c:{color}">'
                f'<div class="label">Promedio por trayectoria</div>'
                f'<div class="value">{promedio:.0f} m</div>'
                f'</div>',
                unsafe_allow_html=True)
