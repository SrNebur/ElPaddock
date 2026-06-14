import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import os


st.image("https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg", width=150)
st.title("🏁 El Paddock: Plataforma de visualización de datos de F1")

st.markdown("""
**Bienvenido al proyecto interactivo de visualización de datos históricos de la Fórmula 1 (1950 - 2025).**

Esta aplicación web ha sido diseñada para explorar visualmente la historia de la categoría reina del automovilismo. A través de mapas interactivos y gráficas dinámicas, podrás descubrir la evolución geográfica del campeonato, comparar las eras de dominio de las escuderías, y analizar el rendimiento histórico de los pilotos y las características de los circuitos.

**📚 Origen de los datos:**
Toda la información visualizada en esta plataforma ha sido extraída y combinada a partir de dos bases de datos públicas alojadas en **Kaggle**: *[Formula 1 World Championship (1950-2025)](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020)* y *[Complete F1 Race Results](https://www.kaggle.com/datasets)*. Los datos originales han sido unificados, limpiados y georreferenciados específicamente para garantizar la precisión de los mapas y gráficas de este proyecto.""")

st.divider()

@st.cache_data
def cargar_y_procesar_datos():
    df = pd.read_csv('datos/f1_race_results_1950_2025.csv')
    
    df['country'] = df['circuit_country'].str.replace('-', ' ').str.title().replace({'United States Of America': 'United States of America'})
    
    mapeo_continentes = {
        'Europa': ['Uk', 'Monaco', 'Switzerland', 'Belgium', 'France', 'Italy', 'Germany', 'Spain', 
                   'Netherlands', 'Austria', 'Portugal', 'Hungary', 'Sweden', 'Russia'],
        'América': ['United States of America', 'Argentina', 'Brazil', 'Canada', 'Mexico'],
        'Asia y Medio Oriente': ['Japan', 'Malaysia', 'Bahrain', 'China', 'Turkey', 'Singapore', 'Uae', 
                 'South Korea', 'India', 'Saudi Arabia', 'Qatar', 'Azerbaijan'],
        'Oceanía': ['Australia'],
        'África': ['South Africa', 'Morocco']
    }
    
    def asignar_continente(pais):
        for continente, paises in mapeo_continentes.items():
            if pais in paises:
                return continente
        return 'Otros'
        
    df['continente'] = df['country'].apply(asignar_continente)
    
    url_mapa = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url_mapa)
    columna_pais = 'ADMIN' if 'ADMIN' in world.columns else 'NAME'
    world = world.rename(columns={columna_pais: 'name'})
    world = world[world['name'] != "Antarctica"]
    
    return df, world

try:
    df_f1, world_map = cargar_y_procesar_datos()
    
    st.subheader("🌍 Evolución geográfica: La expansión del campeonato")
    st.markdown("""
    Para comenzar nuestro recorrido, esta primera sección está dedicada a explorar la expansión geográfica de la Fórmula 1. Aquí podrás analizar cómo el campeonato ha evolucionado desde sus orígenes en 1950, donde se concentraba casi exclusivamente en Europa, hasta convertirse en un evento de magnitud global con presencia en los cinco continentes.
    
    **¿Qué puedes hacer en esta sección?**
    Utiliza el deslizador temporal que encontrarás a continuación para definir un rango histórico específico. Al ajustarlo, verás cómo se actualizan automáticamente dos visualizaciones:
    * 🗺️ **Mapa de coropletas:** Colorea los países según la cantidad de Grandes Premios que han albergado en la época seleccionada. *Tip: Pasa el cursor sobre las regiones coloreadas para ver el desglose exacto de los circuitos.*
    * 📈 **Gráfica de evolución regional:** Justo debajo del mapa, verás trazado el peso (en porcentaje) que ha tenido cada continente en el calendario a lo largo del tiempo.
    """)
    
    anio_min, anio_max = int(df_f1['season'].min()), int(df_f1['season'].max())
    rango_anios = st.slider(
        "Rango Histórico de Visualización:",
        min_value=anio_min, 
        max_value=anio_max, 
        value=(1950, 2025),
        step=1
    )
    
    df_filtrado = df_f1[(df_f1['season'] >= rango_anios[0]) & (df_f1['season'] <= rango_anios[1])]
    df_carreras = df_filtrado.drop_duplicates(subset=['season', 'round_number']).copy()
    
    races_per_country = df_carreras.groupby('country').size().reset_index(name='total_races')
    circuit_counts = df_carreras.groupby(['country', 'circuit_name']).size().reset_index(name='carreras_en_circuito')
    circuit_counts['txt'] = circuit_counts['circuit_name'] + " (" + circuit_counts['carreras_en_circuito'].astype(str) + ")"
    desglose_circuitos = circuit_counts.groupby('country')['txt'].apply(lambda x: ' • ' + '<br> • '.join(x)).reset_index(name='Desglose de Circuitos')
    
    info_final_paises = races_per_country.merge(desglose_circuitos, on='country', how='left')
    world_f1 = world_map.merge(info_final_paises, how='left', left_on='name', right_on='country')
    world_f1['Total Carreras'] = world_f1['total_races'].fillna(0).astype(int)
    world_f1['Desglose de Circuitos'] = world_f1['Desglose de Circuitos'].fillna('Ninguno')
    world_f1['País'] = world_f1['name']
    
    clases_k = 5 if len(races_per_country) >= 5 else len(races_per_country)
    
    mapa_interactivo = world_f1.explore(
        column='total_races',        
        cmap='YlOrRd',               
        scheme='NaturalBreaks',      
        k=clases_k,                         
        tooltip=['País', 'Total Carreras', 'Desglose de Circuitos'], 
        tiles='https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', 
        attr='CartoDB Positron',
        name="Densidad por País",
        legend_kwds=dict(caption=f'Nº Grandes Premios'),
        missing_kwds={'color': '#f2f2f2', 'label': 'Sin carreras'}, 
        max_bounds=True
    )
    
    st_folium(mapa_interactivo, height=500, use_container_width=True, returned_objects=[])

    st.markdown("### 📈 Evolución de la cuota regional del calendario")
    
    region_counts = df_carreras.groupby(['season', 'continente']).size().reset_index(name='count')
    total_counts = df_carreras.groupby('season').size().reset_index(name='total')
    region_pct = region_counts.merge(total_counts, on='season')
    region_pct['porcentaje'] = (region_pct['count'] / region_pct['total']) * 100
    
    fig_lineas = px.line(
        region_pct, 
        x='season', 
        y='porcentaje', 
        color='continente', 
        markers=True, 
        labels={'season': 'Año de la Temporada', 'porcentaje': 'Porcentaje del Calendario (%)', 'continente': 'Continente'},
        color_discrete_sequence=px.colors.qualitative.D3 
    )
    
    fig_lineas.update_layout(
        height=450, 
        margin=dict(t=20, b=10, l=0, r=0),
        yaxis_ticksuffix="%",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
    )
    
    fig_lineas.update_traces(mode='lines+markers', hovertemplate="<b>Año:</b> %{x}<br><b>Cuota:</b> %{y:.1f}%")
    
    st.plotly_chart(fig_lineas, use_container_width=True)

    st.divider()

    st.subheader("🧭 ¡Sigue explorando!")
    st.markdown("""
    El análisis geográfico es solo el punto de partida. Te invitamos a profundizar en las diferentes dimensiones de la Fórmula 1 haciendo clic en los siguientes módulos, donde descubrirás estadísticas detalladas, análisis de rendimiento y mucha más información interactiva. 
    
    *💡 **Nota:** Recuerda que siempre tienes a tu disposición el menú de navegación lateral (a la izquierda de tu pantalla) para desplazarte libremente por todas las páginas disponibles en cualquier momento.*
    """)
    
    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
    
    paginas = os.listdir("pages") if os.path.exists("pages") else []
    arch_pilotos = next((p for p in paginas if "piloto" in p.lower() and p.endswith(".py")), None)
    arch_escud = next((p for p in paginas if "escuderia" in p.lower() and p.endswith(".py")), None)
    arch_circ = next((p for p in paginas if "circuito" in p.lower() and p.endswith(".py")), None)
    arch_temporadas = next((p for p in paginas if "temporada" in p.lower() and p.endswith(".py")), None)
    
    with c_btn1:
        if st.button("🏎️ Visualizar Pilotos", use_container_width=True) and arch_pilotos:
            st.switch_page(f"pages/{arch_pilotos}")
            
    with c_btn2:
        if st.button("🏭 Visualizar Escuderías", use_container_width=True) and arch_escud:
            st.switch_page(f"pages/{arch_escud}")
            
    with c_btn3:
        if st.button("🛣️ Visualizar Circuitos", use_container_width=True) and arch_circ:
            st.switch_page(f"pages/{arch_circ}")
            
    with c_btn4:
        if st.button("📅 Analizar Temporadas", use_container_width=True) and arch_temporadas:
            st.switch_page(f"pages/{arch_temporadas}")

except FileNotFoundError:
    st.error("⚠️ Archivo no encontrado. Asegúrate de tener el CSV en la carpeta 'datos/'.")