import streamlit as st

st.set_page_config(
    page_title="El Paddock",
    page_icon="🏎️",
    layout="wide"
)

if "anio_seleccionado" not in st.session_state:
    st.session_state["anio_seleccionado"] = 2025

page_home = st.Page("pages/home.py", title="Inicio", icon="🏁")
page_circuitos = st.Page("pages/circuitos.py", title="Circuitos", icon="🛣️")
page_pilotos = st.Page("pages/pilotos.py", title="Pilotos", icon="🏎️")
page_escuderias = st.Page("pages/escuderias.py", title="Escuderías", icon="🏭")
page_temporadas = st.Page("pages/temporadas.py", title="Análisis de Temporadas", icon="📅")

pg = st.navigation({
    "Explorador de Datos": [page_home, page_pilotos, page_escuderias, page_circuitos,page_temporadas],
})

pg.run()