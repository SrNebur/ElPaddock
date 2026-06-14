import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.features import DivIcon
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import hashlib

st.title("📅 Análisis y Evolución de Temporadas")

st.markdown("""
**Bienvenido a la sección de Análisis de Temporadas de la Fórmula 1.**

Esta página está diseñada para explorar la evolución del campeonato a través del tiempo, ofreciéndote dos perspectivas visuales complementarias para entender la historia de la categoría:

* 🏁 **Análisis de Temporada Individual:** Sumérgete en el detalle de un año concreto. Visualiza la emocionante batalla por el campeonato carrera a carrera, explora el calendario oficial y descubre la ruta logística que siguen los equipos a través de un mapa interactivo mundial.
* 📈 **Evolución Histórica Multi-año:** Adopta una vista panorámica. Al seleccionar un rango histórico amplio, podrás observar grandes tendencias, como el aumento de los kilómetros recorridos debido a la expansión del calendario, la competitividad de las diferentes épocas y las grandes eras de dominio de las escuderías campeonas.
""")
st.divider()


colores_escuderias = {
    'Ferrari': '#EF1A2D', 'Alfa Romeo': '#900000', 'Maserati': '#CE1126',
    'Red Bull': '#0600EF', 'Williams': '#00A3E0', 'Brabham': '#004225',
    'Matra': '#13447c', 'Tyrrell': '#005AFF', 'March': '#F58220',
    'Mercedes': '#00D2BE', 'Benetton': '#006400', 'Lotus': '#228B22',
    'Vanwall': '#2C4931', 'Toro Rosso': '#4682B4', 'McLaren': '#FF8700',
    'Renault': '#FFF500', 'Brawn': '#B8FD21', 'BRM': '#7B3F00',
    'Cooper': '#314F4F'
}

def obtener_color_escuderia(nombre):
    if pd.isna(nombre):
        return '#808080'
    n = str(nombre).lower()
    for key, color in colores_escuderias.items():
        if key.lower() in n: return color
    if 'alpine' in n: return '#0090FF' 
    if 'aston martin' in n: return '#006F62' 
    if 'force india' in n or 'racing point' in n: return '#F596C8' 
    if 'haas' in n: return '#E6002B'
    if 'sauber' in n or 'alfa romeo' in n: return '#900000'
    
    paleta_fallback = px.colors.qualitative.Alphabet
    hash_idx = int(hashlib.md5(str(nombre).encode('utf-8')).hexdigest(), 16)
    return paleta_fallback[hash_idx % len(paleta_fallback)]

def calcular_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1)/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1)/2)**2
    return R * (2 * np.arcsin(np.sqrt(a)))

def acortar_nombre_piloto(nombre):
    partes = str(nombre).split()
    if len(partes) > 1:
        return f"{partes[0][0]}. {' '.join(partes[1:])}"
    return str(nombre)

@st.cache_data
def cargar_y_procesar_datos():
    ruta_datos = "datos/"
    df = pd.read_csv(os.path.join(ruta_datos, "f1_race_results_1950_2025.csv"))
    
    df['country'] = df['circuit_country'].str.replace('-', ' ').str.title().replace({'United States Of America': 'United States of America'})
    df['race_date'] = pd.to_datetime(df['race_date'], errors='coerce')
    df['driver_name_short'] = df['driver_name'].apply(acortar_nombre_piloto)
    
    mapeo_continentes = {
        'Europe': ['Uk', 'Great Britain', 'Monaco', 'Switzerland', 'Belgium', 'France', 'Italy', 
                   'San Marino', 'Germany', 'Spain', 'Netherlands', 'Austria', 'Portugal', 
                   'Hungary', 'Sweden', 'Russia', 'Turkey', 'Luxembourg'],
        'Americas': ['United States of America', 'United States', 'Usa', 'Argentina', 'Brazil', 
                     'Canada', 'Mexico'],
        'Asia': ['Japan', 'Malaysia', 'Bahrain', 'China', 'Singapore', 'Uae', 
                 'United Arab Emirates', 'South Korea', 'Korea', 'India', 'Saudi Arabia', 
                 'Qatar', 'Azerbaijan', 'Vietnam', 'Thailand'],
        'Oceania': ['Australia', 'New Zealand'],
        'Africa': ['South Africa', 'Morocco']
    }
    
    def asignar_continente(pais):
        for cont, paises in mapeo_continentes.items():
            if pais in paises: return cont
        return 'Otros'
        
    df['continente'] = df['country'].str.strip().apply(asignar_continente)
    return df

@st.cache_data
def calcular_metricas_globales(df):
    resultados = []
    for year in df['season'].unique():
        df_anio = df[df['season'] == year]
        
        calendario = df_anio.drop_duplicates(subset=['round_number']).sort_values('round_number').dropna(subset=['circuit_latitude', 'circuit_longitude'])
        num_carreras = len(calendario)
        dist = sum(calcular_haversine(calendario.iloc[i]['circuit_latitude'], calendario.iloc[i]['circuit_longitude'], 
                                      calendario.iloc[i+1]['circuit_latitude'], calendario.iloc[i+1]['circuit_longitude']) 
                   for i in range(len(calendario)-1)) if len(calendario) > 1 else 0
        
        ganadores = df_anio[df_anio['finish_position_num'] == 1]
        pilotos_ganadores = ganadores['driver_name'].nunique()
        
        pts_pilotos = df_anio.groupby('driver_name_short')['points'].sum()
        campeon_piloto = pts_pilotos.idxmax() if not pts_pilotos.empty else "N/A"
        
        if year >= 1958:
            pts_const = df_anio.groupby('constructor_name')['points'].sum()
            campeon_const = pts_const.idxmax() if not pts_const.empty else "N/A"
        else:
            campeon_const = "No existía el campeonato"
            
        resultados.append({
            'season': year, 'distancia_km': dist, 'num_carreras': num_carreras,
            'pilotos_ganadores': pilotos_ganadores, 'campeon_piloto': campeon_piloto,
            'campeon_constructor': campeon_const
        })
        
    return pd.DataFrame(resultados)


try:
    df_f1 = cargar_y_procesar_datos()
    df_metricas = calcular_metricas_globales(df_f1)
    
    tab1, tab2 = st.tabs(["🏁 Análisis de temporada individual", "📈 Evolución histórica multi-año"])
    
    # =========================================================
    # ANALISIS DE TEMPORADA INDIVIDUAL
    # =========================================================
    with tab1:
        st.subheader("Radiografía detallada de la temporada")
        anio_sel = st.selectbox("Selecciona la temporada a analizar:", sorted(df_f1['season'].unique(), reverse=True))
        df_anio = df_f1[df_f1['season'] == anio_sel]
        
        def plot_acumulado(df_year, entidad, titulo, is_constructor=False):
            pts_ronda = df_year.groupby(['round_number', entidad])['points'].sum().reset_index()
            pts_pivot = pts_ronda.pivot(index='round_number', columns=entidad, values='points').fillna(0)
            pts_acum = pts_pivot.cumsum()
            
            pts_acum = pts_acum.replace(0, np.nan)
            
            orden_participantes = pts_acum.iloc[-1].sort_values(ascending=False).index.tolist()
            top5 = orden_participantes[:5]
            
            pts_acum_melt = pts_acum.reset_index().melt(id_vars='round_number', var_name='Participante', value_name='Puntos')
            
            color_map = {esc: obtener_color_escuderia(esc) for esc in df_year[entidad].unique()} if is_constructor else None
            color_seq = px.colors.qualitative.Alphabet if not is_constructor else None
            
            fig = px.line(pts_acum_melt, x='round_number', y='Puntos', color='Participante', 
                          title=titulo, color_discrete_map=color_map, color_discrete_sequence=color_seq,
                          category_orders={"Participante": orden_participantes})
            
            fig.for_each_trace(lambda trace: trace.update(visible="legendonly") if trace.name not in top5 else ())
            fig.update_layout(xaxis_title="Ronda del Campeonato", yaxis_title="Puntos Totales", height=500)
            return fig

        st.markdown("""
        **🏆 Evolución del Mundial de Pilotos** *Observa el desarrollo del campeonato carrera a carrera. Por defecto se muestran las curvas de los 5 mejores pilotos al final del año. (Puedes hacer clic en la leyenda para mostrar u ocultar corredores).*
        """)
        st.plotly_chart(plot_acumulado(df_anio, 'driver_name_short', ''), use_container_width=True)
        
        if anio_sel >= 1958:
            st.markdown("""
            **🛡️ Evolución del Mundial de Constructores** *Al igual que en el campeonato de pilotos, esta gráfica ilustra el rendimiento acumulado de las escuderías. La constancia de los dos coches del equipo es clave para dominar este campeonato.*
            """)
            st.plotly_chart(plot_acumulado(df_anio, 'constructor_name', '', is_constructor=True), use_container_width=True)
        else:
            st.info("ℹ️ **Contexto Histórico:** El Campeonato Mundial de Constructores no se introdujo oficialmente hasta la temporada **1958**. Por lo tanto, no hay registros de puntos por escuderías para este año.")

        st.divider()

        st.subheader("📅 Calendario Oficial Interactivo")
        st.markdown("*Tabla detallada con todas las carreras disputadas en la temporada. Utiliza los filtros para buscar Grandes Premios específicos o acotar por un rango de fechas concreto.*")
        
        calendario = df_anio.drop_duplicates(subset=['round_number']).sort_values('round_number')

        col_filtro1, col_filtro2 = st.columns(2)
        paises_sel = col_filtro1.multiselect("Filtrar por País:", calendario['country'].unique(), default=[])
        min_date, max_date = calendario['race_date'].min(), calendario['race_date'].max()
        rango_fechas = col_filtro2.date_input("Rango de Fechas:", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        
        df_filtro = calendario.copy()
        if paises_sel: df_filtro = df_filtro[df_filtro['country'].isin(paises_sel)]
        if len(rango_fechas) == 2: df_filtro = df_filtro[(df_filtro['race_date'].dt.date >= rango_fechas[0]) & (df_filtro['race_date'].dt.date <= rango_fechas[1])]
        
        df_mostrar = df_filtro[['round_number', 'country', 'circuit_name', 'race_date']].rename(
            columns={'round_number':'Ronda', 'country':'País', 'circuit_name':'Circuito', 'race_date':'Fecha'}
        )
        df_mostrar['Fecha'] = pd.to_datetime(df_mostrar['Fecha']).dt.strftime('%d/%m/%Y')
        st.dataframe(df_mostrar, hide_index=True, use_container_width=True)

        st.divider()
        
        st.subheader("🌍 Análisis Logístico: La Ruta Mundial")
        st.markdown("""
        *Este mapa traza la ruta estimada que recorrieron los equipos a lo largo del año. Los largos desplazamientos entre rondas consecutivas reflejan el enorme desafío logístico que supone organizar un mundial en múltiples continentes. Los marcadores numerados indican el orden cronológico de los Grandes Premios.*
        """)
        
        
        df_coords = calendario.dropna(subset=['circuit_latitude', 'circuit_longitude'])
        
        distancia_total = 0
        coords = []
        nombres = []
        
        if len(df_coords) >= 2:
            coords = df_coords[['circuit_latitude', 'circuit_longitude']].values.tolist()
            nombres = df_coords['circuit_name'].tolist()
            distancia_total = sum(calcular_haversine(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1]) for i in range(len(coords)-1))
        
        st.info(f"**✈️ Distancia Logística Estimada (Solo trayectos entre Grandes Premios):** `{distancia_total:,.0f} km`".replace(",", "."))
        
        mapa_logistica = folium.Map(
            location=[25, 0], zoom_start=2, min_zoom=1.5, max_bounds=True,
            tiles='https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', 
            attr='CartoDB Positron (No Labels)'
        )
        
        if len(coords) >= 2:
            folium.PolyLine(coords, color="#FF1801", weight=2.5, opacity=0.8).add_to(mapa_logistica)
            for i, (lat, lon) in enumerate(coords):
                round_num = i + 1
                icon_html = f"""
                    <div style="background-color: #FF1801; border: 2px solid white; border-radius: 50%;
                        width: 20px; height: 20px; display: flex; align-items: center; justify-content: center;
                        color: white; font-weight: bold; font-size: 8px; box-shadow: 0px 0px 4px rgba(0,0,0,0.4);">
                        {round_num}
                    </div>
                """
                folium.Marker(
                    location=[lat, lon], icon=DivIcon(html=icon_html),
                    tooltip=f"<b>{anio_sel} - Ronda {round_num}</b><br>{nombres[i]}"
                ).add_to(mapa_logistica)
        
        st_folium(mapa_logistica, height=500, use_container_width=True, returned_objects=[])
        
        
        

    # =========================================================
    # EVOLUCION HISTORICA MULTI-AÑO
    # =========================================================
    with tab2:
        st.subheader("Evolución histórica del deporte")
        min_y, max_y = int(df_f1['season'].min()), int(df_f1['season'].max())
        
        rango_hist = st.slider("Selecciona el rango de años a analizar:", min_value=min_y, max_value=max_y, value=(min_y, max_y))
        
        df_rango = df_f1[(df_f1['season'] >= rango_hist[0]) & (df_f1['season'] <= rango_hist[1])]
        df_met_rango = df_metricas[(df_metricas['season'] >= rango_hist[0]) & (df_metricas['season'] <= rango_hist[1])]
        
        st.markdown("### 🏆 Cuadro de honor")
        st.markdown("*Un rápido repaso a los campeones absolutos de cada temporada dentro del rango seleccionado. Representa la combinación perfecta entre el talento del piloto y el diseño del monoplaza.*")
        
        df_cuadro = df_met_rango[['season', 'campeon_piloto', 'campeon_constructor']].sort_values('season', ascending=False)
        df_cuadro.columns = ['Temporada', 'Piloto Campeón', 'Escudería Campeona']
        st.dataframe(df_cuadro, hide_index=True, use_container_width=True)
        st.divider()

        st.markdown("### 🛡️ Eras de Dominio")
        st.markdown("*Esta visualización destaca los periodos de hegemonía en la Fórmula 1. Cada línea continua representa una racha o era en la que una misma escudería se alzó con el campeonato de constructores, permitiendo identificar rápidamente los ciclos históricos.*")
        
        df_eras = df_met_rango[(df_met_rango['season'] >= 1958) & 
                               (df_met_rango['season'] >= rango_hist[0]) & 
                               (df_met_rango['season'] <= rango_hist[1])].copy()
        
        if not df_eras.empty:
            df_eras = df_eras.sort_values('season') 
            
            df_eras['racha_id'] = (df_eras['campeon_constructor'] != df_eras['campeon_constructor'].shift()).cumsum()
            
            primer_camp = df_eras.groupby('campeon_constructor')['season'].min().sort_values().index.tolist()
            mapa_colores_real = {esc: obtener_color_escuderia(esc) for esc in df_eras['campeon_constructor'].unique()}
            
            fig_hegemonia = px.line(
                df_eras, x='season', y='campeon_constructor', color='campeon_constructor',
                line_group='racha_id',
                color_discrete_map=mapa_colores_real, markers=True,
                labels={'season': 'Temporada', 'campeon_constructor': 'Escudería'}
            )
            
            # Reducimos el ancho de la línea de 4 a 2
            fig_hegemonia.update_traces(line=dict(width=2), marker=dict(size=14, line=dict(width=1.5, color='DarkSlateGrey')))
            fig_hegemonia.update_yaxes(categoryorder='array', categoryarray=primer_camp)
            fig_hegemonia.update_layout(height=600, showlegend=False, margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(tickmode='linear', dtick=4))
            fig_hegemonia.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.2)')
            st.plotly_chart(fig_hegemonia, use_container_width=True)
        else:
            st.warning("Selecciona un rango a partir de 1958 para visualizar las eras de dominio de constructores.")
        st.divider()

        st.markdown("### ⚔️ Índice de Competitividad ")
        st.markdown("*Esta métrica evalúa la igualdad de la parrilla. Un número alto de ganadores distintos indica una temporada impredecible y reñida, mientras que valores bajos reflejan el dominio aplastante de uno o dos monoplazas sobre el resto.*")
        
        fig_comp = px.line(df_met_rango, x='season', y='pilotos_ganadores', markers=True,
                           labels={'season': 'Año', 'pilotos_ganadores': 'Nº de Pilotos Diferentes con Victoria'},
                           color_discrete_sequence=["#2E86C1"], height=400)
        fig_comp.update_yaxes(dtick=1)
        st.plotly_chart(fig_comp, use_container_width=True)
        st.divider()

        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.markdown("### ✈️ El desafío logístico")
            st.markdown("*Compara el número de Grandes Premios celebrados con los kilómetros logísticos estimados. Observa cómo el crecimiento y la globalización del calendario moderno han aumentado drásticamente las distancias de viaje de los equipos.*")
            
            fig_log = make_subplots(specs=[[{"secondary_y": True}]])
            fig_log.add_trace(go.Bar(x=df_met_rango['season'], y=df_met_rango['num_carreras'], name="Grandes Premios", marker_color='rgba(150, 150, 150, 0.5)'), secondary_y=False)
            fig_log.add_trace(go.Scatter(x=df_met_rango['season'], y=df_met_rango['distancia_km'], name="Kilómetros", mode="lines+markers", line=dict(color="#FF1801", width=3)), secondary_y=True)
            
            fig_log.update_layout(height=450, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(t=20))
            fig_log.update_yaxes(title_text="Nº de Carreras", secondary_y=False)
            fig_log.update_yaxes(title_text="Kilómetros Recorridos", secondary_y=True)
            st.plotly_chart(fig_log, use_container_width=True)
            
        with col_m2:
            st.markdown("### 🌍 Expansión por regiones")
            st.markdown("*Analiza la cuota geográfica del calendario. Observa cómo el campeonato inicial, mayormente europeo, ha ido cediendo espacio para dar paso a un calendario verdaderamente global.*")
            
            carreras_region = df_rango.drop_duplicates(subset=['season', 'round_number']).groupby(['season', 'continente']).size().reset_index(name='carreras')
            fig_area = px.area(carreras_region, x='season', y='carreras', color='continente', 
                               labels={'season': '', 'carreras': 'Nº de Grandes Premios', 'continente': 'Continente'}, height=450)
            
            fig_area.update_traces(line=dict(width=0))
            fig_area.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(t=20))
            st.plotly_chart(fig_area, use_container_width=True)

except FileNotFoundError:
    st.error("⚠️ Archivo 'f1_race_results_1950_2025.csv' no encontrado.")