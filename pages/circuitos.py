import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import os
import hashlib

st.title("🛣️ Circuitos y Trazados")
st.markdown("""
**Bienvenido a la sección dedicada a los circuitos de la Fórmula 1.**

Explora a fondo cada escenario que ha formado parte del campeonato. Esta página te permite interactuar con los datos para conocer la ubicación de cualquier trazado, visualizar cómo suelen desarrollarse sus carreras y repasar qué pilotos y escuderías han conquistado cada Gran Premio a lo largo de su historia.
""")

colores_escuderias = {
    'Ferrari': '#FF2400', 'Alfa Romeo': '#D50000', 'Maserati': '#E53935',
    'Red Bull': '#1E88E5', 'Williams': '#00B0FF', 'Brabham': '#00E676',
    'Matra': '#29B6F6', 'Tyrrell': '#2979FF', 'March': '#FF9100',
    'Mercedes': '#00E5FF', 'Benetton': '#00C853', 'Lotus': '#FFEA00',
    'Vanwall': '#69F0AE', 'Toro Rosso': '#4FC3F7', 'McLaren': '#FF6D00',
    'Renault': '#FFD600', 'Brawn': '#C6FF00', 'BRM': '#BCAAA4',
    'Cooper': '#26A69A', 'Aston Martin': '#1DE9B6', 'Alpine': '#40C4FF',
    'Sauber': '#FF1744', 'Haas': '#FF5252', 'Racing Point': '#FF80AB',
    'Force India': '#FF80AB', 'AlphaTauri': '#ECEFF1', 'Honda': '#FFFFFF'
}

def obtener_color_escuderia(nombre):
    if pd.isna(nombre): return '#B0BEC5'
    n = str(nombre).lower()
    for key, color in colores_escuderias.items():
        if key.lower() in n: return color
    
    paleta_fallback = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel1
    hash_idx = int(hashlib.md5(str(nombre).encode('utf-8')).hexdigest(), 16)
    return paleta_fallback[hash_idx % len(paleta_fallback)]

@st.cache_data
def cargar_datos_circuitos():
    ruta_datos = "datos/"
    df = pd.read_csv(os.path.join(ruta_datos, "f1_race_results_1950_2025.csv"))
    
    df['country_eng'] = df['circuit_country'].str.replace('-', ' ').str.title()
    df['country_eng'] = df['country_eng'].replace({'United States Of America': 'United States', 'Usa': 'United States', 'Uk': 'United Kingdom'})
    
    mapeo_paises_es = {
        'Spain': 'España', 'United Kingdom': 'Reino Unido', 'Great Britain': 'Reino Unido', 'Germany': 'Alemania', 
        'France': 'Francia', 'Italy': 'Italia', 'Brazil': 'Brasil', 'Argentina': 'Argentina', 
        'Austria': 'Austria', 'Australia': 'Australia', 'Canada': 'Canadá', 'Japan': 'Japón', 
        'Netherlands': 'Países Bajos', 'Mexico': 'México', 'Monaco': 'Mónaco', 'Belgium': 'Bélgica', 
        'United States': 'Estados Unidos', 'Switzerland': 'Suiza', 'Sweden': 'Suecia', 'South Africa': 'Sudáfrica', 
        'China': 'China', 'Russia': 'Rusia', 'India': 'India', 'Portugal': 'Portugal', 'Malaysia': 'Malasia', 
        'Hungary': 'Hungría', 'Finland': 'Finlandia', 'Bahrain': 'Bahréin', 'Saudi Arabia': 'Arabia Saudita', 
        'Uae': 'Abu Dabi', 'United Arab Emirates': 'Abu Dabi', 'Singapore': 'Singapur', 'Azerbaijan': 'Azerbaiyán',
        'Qatar': 'Catar', 'Turkey': 'Turquía', 'South Korea': 'Corea del Sur', 'Morocco': 'Marruecos'
    }
    df['country'] = df['country_eng'].replace(mapeo_paises_es)
    
    df['race_date'] = pd.to_datetime(df['race_date'], errors='coerce')
    df['grid_position'] = pd.to_numeric(df['grid_position'], errors='coerce')
    df['finish_position_num'] = pd.to_numeric(df['finish_position_num'], errors='coerce')
    
    return df

try:
    df_f1 = cargar_datos_circuitos()

    st.sidebar.header("⚙️ Filtros del circuito")
    
    paises_disponibles = sorted(df_f1['country'].dropna().unique())
    
    if 'filtro_pais_circuito' not in st.session_state:
        st.session_state['filtro_pais_circuito'] = 'Todos'
    
    pais_sel = st.sidebar.selectbox(
        "1. Selecciona el país:", 
        ['Todos'] + paises_disponibles, 
        key='filtro_pais_circuito'
    )
    
    if pais_sel == 'Todos':
        df_pais = df_f1.copy()
    else:
        df_pais = df_f1[df_f1['country'] == pais_sel]
        
    circuitos_disponibles = sorted(df_pais['circuit_name'].dropna().unique())
    
    circuito_actual = st.session_state.get('selector_circuito', '')
    
    if circuito_actual not in circuitos_disponibles:
        favoritos_circ = ["Autodromo Nazionale Di Monza", "Silverstone Circuit", "Circuit De Monaco", "Circuit De Spa-Francorchamps"]
        encontrado = False
        for fav in favoritos_circ:
            if fav in circuitos_disponibles:
                st.session_state['selector_circuito'] = fav
                encontrado = True
                break
        if not encontrado and circuitos_disponibles:
            st.session_state['selector_circuito'] = circuitos_disponibles[0]
            
    circuito_sel = st.sidebar.selectbox(
        "2. Selecciona el circuito:", 
        circuitos_disponibles, 
        key='selector_circuito'
    )
    
    df_circuito = df_f1[df_f1['circuit_name'] == circuito_sel]
    
    min_y, max_y = int(df_circuito['season'].min()), int(df_circuito['season'].max())
    if min_y == max_y:
        st.sidebar.info(f"Solo se disputó una carrera en este circuito ({min_y}).")
        rango_anios = (min_y, max_y)
    else:
        rango_anios = st.sidebar.slider("3. Rango temporal:", min_value=min_y, max_value=max_y, value=(min_y, max_y))

    df_filtrado = df_circuito[(df_circuito['season'] >= rango_anios[0]) & (df_circuito['season'] <= rango_anios[1])]

    st.divider()
    st.subheader("📍 Ficha del circuito")
    
    col_metricas, col_mapa = st.columns([1, 1.5])
    
    with col_metricas:
        total_gps = df_filtrado['season'].nunique()
        primer_gp = df_circuito['season'].min()
        localidad = df_circuito['circuit_place'].iloc[0]
        pais_real = df_circuito['country'].iloc[0]
        
        st.metric("Total grandes premios", total_gps)
        st.metric("Inauguración en F1", primer_gp)
        st.metric("Ubicación", f"{localidad}, {pais_real}")
        
    with col_mapa:
        lat = df_circuito['circuit_latitude'].iloc[0]
        lon = df_circuito['circuit_longitude'].iloc[0]
        
        mapa_circuito = folium.Map(
            location=[lat, lon], zoom_start=13,
            tiles='https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', 
            attr='CartoDB Positron (No Labels)',
            max_bounds=True, min_lat=-85, max_lat=85, min_lon=-180, max_lon=180
        )
        
        folium.Marker(
            location=[lat, lon],
            tooltip=f"<div style='font-family: sans-serif; text-align: center;'><b>{circuito_sel}</b></div>",
            icon=folium.Icon(color="red", icon="flag", prefix="fa")
        ).add_to(mapa_circuito)
        
        st_folium(mapa_circuito, height=250, use_container_width=True, returned_objects=[])

    st.divider()

    st.subheader(f"🏆 Historia en el periodo seleccionado ({rango_anios[0]} - {rango_anios[1]})")
        
    col_palmares, col_dominio = st.columns([1.2, 1])
    
    with col_palmares:
        st.markdown("**Palmarés de ganadores**")
        ganadores_palmares = df_filtrado[df_filtrado['finish_position_num'] == 1]
        if not ganadores_palmares.empty:
            palmares = ganadores_palmares[['season', 'driver_name', 'constructor_name']].sort_values('season', ascending=False)
            palmares.columns = ['Año', 'Piloto Ganador', 'Escudería']
            st.dataframe(palmares, hide_index=True, use_container_width=True)
        else:
            st.write("Sin datos de ganadores en este periodo.")
            
    with col_dominio:
        st.markdown("**Hegemonía de escuderías en este circuito**")
        if not ganadores_palmares.empty:
            victorias_eq = ganadores_palmares['constructor_name'].value_counts().reset_index()
            victorias_eq.columns = ['Escudería', 'Victorias']
            
            color_map = {esc: obtener_color_escuderia(esc) for esc in victorias_eq['Escudería']}
            
            fig_bar = px.bar(
                victorias_eq.head(10), x='Victorias', y='Escudería', orientation='h',
                color='Escudería', color_discrete_map=color_map
            )
            
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, height=350, margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

    if not df_filtrado.empty:
        st.divider()
        st.subheader("🏎️ Dinámica del circuito")
        st.markdown("*Esta visualización relaciona la posición de salida con la posición de llegada. Nos ayuda a descubrir visualmente si estamos ante un trazado donde priman los adelantamientos y las remontadas, o si es un circuito donde la clasificación del sábado suele dictar el resultado final de la carrera.*")
        
        df_pred = df_filtrado.dropna(subset=['grid_position', 'finish_position_num']).copy()
        df_pred = df_pred[(df_pred['grid_position'] > 0)]
        
        col_scatter, col_texto = st.columns([1.5, 1.5]) 
        
        with col_scatter:
            df_pred['grid_position'] = df_pred['grid_position'].astype(int)
            df_pred['finish_position_num'] = df_pred['finish_position_num'].astype(int)
            
            df_pred['grid_jitter'] = df_pred['grid_position'] + np.random.uniform(-0.2, 0.2, size=len(df_pred))
            df_pred['finish_jitter'] = df_pred['finish_position_num'] + np.random.uniform(-0.2, 0.2, size=len(df_pred))
            
            fig_scatter = px.scatter(
                df_pred, x='grid_jitter', y='finish_jitter', 
                hover_data={
                    'grid_jitter': False, 
                    'finish_jitter': False,
                    'season': True,
                    'driver_name': True,
                    'grid_position': True,
                    'finish_position_num': True
                },
                labels={
                    'grid_position': 'Salió', 
                    'finish_position_num': 'Llegó',
                    'season': 'Año',
                    'driver_name': 'Piloto'
                },
                opacity=0.7, color_discrete_sequence=['#00E5FF'] 
            )
            
            max_pos = max(df_pred['grid_position'].max(), df_pred['finish_position_num'].max())
            fig_scatter.add_trace(go.Scatter(
                x=[1, max_pos], y=[1, max_pos], mode='lines', 
                name="Línea de 0 Adelantamientos", line=dict(color="#AF2C46", dash='dash') 
            ))
            
            fig_scatter.update_layout(
                xaxis_title="Posición de Salida (Grid)",
                yaxis_title="Posición Final",
                height=400, 
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with col_texto:
            ganadores = df_pred[df_pred['finish_position_num'] == 1]
            
            media_salida_ganador = ganadores['grid_position'].mean() if not ganadores.empty else 0
            indice_remontada = media_salida_ganador - 1.0 if not ganadores.empty else 0
            
            df_pred['movimiento_absoluto'] = abs(df_pred['grid_position'] - df_pred['finish_position_num'])
            movilidad_media = df_pred['movimiento_absoluto'].mean()

            if len(ganadores) < 5:
                st.warning("⚠️ **Muestra Estadística Insuficiente**\n\nMenos de 5 GPs en el rango seleccionado. Los datos pueden estar sesgados.")
            else:
                st.markdown("### Índices de acción visualizados")
                
                col_ind1, col_ind2 = st.columns(2)
                
                with col_ind1:
                    st.metric("Remontada Media (Ganador)", f"{indice_remontada:.2f}", help="Media de posiciones que ha tenido que remontar el piloto que finalmente gana la carrera.")
                    if indice_remontada <= 1.4:
                        st.error("**🔴 Ganador predecible**\n\nHistóricamente, es casi imposible ganar si no sales en la primera fila de la parrilla.")
                    elif 1.4 < indice_remontada <= 2.5:
                        st.warning("**🟡 Liderato disputado**\n\nEl circuito permite remontadas hacia la victoria con una buena estrategia de carrera.")
                    else:
                        st.success("**🟢 Finales abiertos**\n\nGanar saliendo desde la segunda fila o más atrás es algo habitual en este escenario.")    
                
                with col_ind2:
                    st.metric("Movilidad Global (Pelotón)", f"{movilidad_media:.2f}", help="Media de posiciones que gana o pierde cualquier piloto durante el transcurso de la carrera.")
                    if movilidad_media < 3.0:
                        st.error("🚂 **Carrera estática**\n\nCircuito cerrado. Las posiciones apenas varían respecto a la parrilla de salida.")
                    else:
                        st.success("⚔️ **Carrera dinámica**\n\nMucho intercambio de posiciones y batallas a lo largo de toda la zona media.")


except FileNotFoundError:
    st.error("⚠️ Archivo 'f1_race_results_1950_2025.csv' no encontrado.")