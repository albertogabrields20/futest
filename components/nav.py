import streamlit as st


def nav_controls(key, n_frames):
    """
    Patrón correcto para botones + slider sincronizados en Streamlit.
    El slider NO usa key — su value viene siempre de session_state.
    Los botones modifican session_state y hacen st.rerun().
    """
    if key not in st.session_state:
        st.session_state[key] = 0

    # Botones ANTES del slider — modifican state y rerrun
    col_prev, col_next, col_info = st.columns([1, 1, 6])
    with col_prev:
        if st.button("◀ Anterior", key=f"{key}_prev", use_container_width=True):
            st.session_state[key] = max(0, st.session_state[key] - 1)
            st.rerun()
    with col_next:
        if st.button("Siguiente ▶", key=f"{key}_next", use_container_width=True):
            st.session_state[key] = min(n_frames - 1, st.session_state[key] + 1)
            st.rerun()
    with col_info:
        st.caption(f"Frame **{st.session_state[key]}** de {n_frames - 1}")

    # Slider SIN key — value siempre desde session_state
    val = st.slider(
        "Frame",
        min_value=0,
        max_value=n_frames - 1,
        value=st.session_state[key],
    )

    # Si el usuario movió el slider, actualizar state
    if val != st.session_state[key]:
        st.session_state[key] = val

    return st.session_state[key]
