import streamlit as st
from ..field import TEAM_COLORS, TEAM_NAMES


def render(players_by_team, distances):
    st.subheader("Distancia recorrida por equipo")

    c1, c2 = st.columns(2)
    for col, team_id in zip([c1, c2], [0, 1]):
        with col:
            color = TEAM_COLORS[team_id]
            pids = sorted(players_by_team[team_id],
                          key=lambda p: distances.get(p, 0), reverse=True)
            total = sum(distances.get(p, 0) for p in pids)

            st.markdown(
                f'<div class="metric-card" style="--c:{color}">'
                f'<div class="label">Total {TEAM_NAMES[team_id]}</div>'
                f'<div class="value">{total:.0f} m</div>'
                f'<div class="sub">{len(pids)} trayectorias</div>'
                f'</div>', unsafe_allow_html=True)

            if not pids:
                st.caption("Sin jugadores detectados")
                continue

            st.markdown(f'<h4 style="color:{color};margin-top:12px">'
                        f'{TEAM_NAMES[team_id]}</h4>', unsafe_allow_html=True)
            max_d = distances.get(pids[0], 1) or 1
            for pid in pids:
                d = distances.get(pid, 0)
                pct = d / max_d * 100
                st.markdown(
                    f'<div style="margin-bottom:10px">'
                    f'<div style="display:flex;justify-content:space-between;'
                    f'font-size:13px;color:#aaa;margin-bottom:3px">'
                    f'<span>ID {pid}</span>'
                    f'<span style="font-weight:600;color:#f0f0f0">{d} m</span></div>'
                    f'<div style="background:#2a2d3e;border-radius:4px;height:7px">'
                    f'<div style="background:{color};width:{pct:.1f}%;'
                    f'height:7px;border-radius:4px"></div>'
                    f'</div></div>', unsafe_allow_html=True)

    st.info("📌 Las estadísticas individuales mejorarán con el tracking corregido.")
