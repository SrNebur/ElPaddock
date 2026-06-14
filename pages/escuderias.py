import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import hashlib
import requests

st.title("🏭 Historia y Legado de las Escuderías")
st.markdown("""
**Bienvenido a la sección dedicada a los equipos constructores de la Fórmula 1.**

Descubre la evolución de las marcas que han dado vida a los monoplazas más icónicos de la historia. A través de estas visualizaciones, podrás explorar sus épocas doradas, comprobar en qué países han logrado más victorias, analizar la fiabilidad mecánica de sus coches y repasar qué leyendas del volante han defendido sus colores.
""")

# CSS para métricas adaptables
st.markdown("""
<style>
[data-testid="stMetricValue"] {
    white-space: normal !important;
    word-wrap: break-word !important;
    font-size: 1.5rem !important;
    line-height: 1.2 !important;
}
</style>
""", unsafe_allow_html=True)

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

# --- API DE WIKIPEDIA ---
@st.cache_data(show_spinner=False)
def obtener_imagen_wikipedia(nombre_equipo):
    headers = {"User-Agent": "F1DashboardApp/1.0"}
    url_search = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={nombre_equipo} Formula 1 constructor&utf8=&format=json"
    try:
        res = requests.get(url_search, headers=headers, timeout=3).json()
        if res['query']['search']:
            titulo_exacto = res['query']['search'][0]['title']
            url_img = f"https://en.wikipedia.org/w/api.php?action=query&titles={titulo_exacto}&prop=pageimages&format=json&pithumbsize=500"
            res_img = requests.get(url_img, headers=headers, timeout=3).json()
            pages = res_img['query']['pages']
            for page_id in pages:
                if 'thumbnail' in pages[page_id]: return pages[page_id]['thumbnail']['source']
    except: pass
    return None


def calcular_etapas_activas(temporadas):
    temps = sorted(list(set(temporadas)))
    if not temps: return ""
    etapas = []
    inicio = temps[0]
    fin = temps[0]
    
    for t in temps[1:]:
        if t == fin + 1:
            fin = t
        else:
            etapas.append(f"{inicio}-{fin}" if inicio != fin else str(inicio))
            inicio = t
            fin = t
            
    etapas.append(f"{inicio}-{fin}" if inicio != fin else str(inicio))
    return ", ".join(etapas)

@st.cache_data
def cargar_datos_escuderias():
    ruta_datos = "datos/"
    df = pd.read_csv(os.path.join(ruta_datos, "f1_race_results_1950_2025.csv"))
    
    df['country_eng'] = df['circuit_country'].astype(str).str.strip().str.title().str.replace('-', ' ')
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
    df['country_es'] = df['country_eng'].replace(mapeo_paises_es)
    
    df['race_date'] = pd.to_datetime(df['race_date'], errors='coerce')
    df['finish_position_num'] = pd.to_numeric(df['finish_position_num'], errors='coerce')
    
    ultima_temp = df['season'].max()
    equipos_activos = df[df['season'] >= (ultima_temp - 1)]['constructor_name'].unique()
    df['estado_equipo'] = df['constructor_name'].apply(lambda x: 'Actual' if x in equipos_activos else 'Inactiva')
    
    df_puntos = df[df['season'] >= 1958].groupby(['season', 'constructor_name'])['points'].sum().reset_index()
    if not df_puntos.empty:
        idx_camp = df_puntos.groupby('season')['points'].idxmax()
        dict_campeones = df_puntos.loc[idx_camp]['constructor_name'].value_counts().to_dict()
    else:
        dict_campeones = {}
        
    df_stats = df.groupby('constructor_name').agg(
        victorias=('finish_position_num', lambda x: (x == 1).sum()),
        carreras=('race_date', 'nunique'), # Aquí estaba el error
        debut=('season', 'min')
    ).reset_index()
    
    def clasificar_exito_estricto(row):
        if dict_campeones.get(row['constructor_name'], 0) > 0:
            return '🏆 Campeones del Mundo'
        elif row['victorias'] > 0:
            return '🥇 Ganadores de Gran Premio'
        elif row['carreras'] >= 50:
            return '🏎️ Escuderías Asentadas (>50 GPs)'
        else:
            return '🔧 Equipos Fugaces (<50 GPs)'
            
    df_stats['categoria_exito'] = df_stats.apply(clasificar_exito_estricto, axis=1)
    
    df_stats['decada_debut'] = (df_stats['debut'] // 10) * 10
    df_stats['decada_str'] = df_stats['decada_debut'].astype(str) + "s"
    
    df = df.merge(df_stats[['constructor_name', 'categoria_exito', 'decada_str']], on='constructor_name', how='left')
    
    return df

try:
    df_f1 = cargar_datos_escuderias()

    st.sidebar.header("⚙️ Filtros de Escuderías")

    if 'escuderia_externa' in st.session_state:
        st.session_state['filtro_cat_eq'] = 'Todas'
        st.session_state['filtro_dec_eq'] = 'Todas'
        st.session_state['filtro_est_eq'] = 'Todos'
        st.session_state['selector_equipo'] = st.session_state['escuderia_externa']
        del st.session_state['escuderia_externa']

    if 'filtro_cat_eq' not in st.session_state: st.session_state['filtro_cat_eq'] = 'Todas'
    if 'filtro_dec_eq' not in st.session_state: st.session_state['filtro_dec_eq'] = 'Todas'
    if 'filtro_est_eq' not in st.session_state: st.session_state['filtro_est_eq'] = 'Todos'
    
    categorias = ['Todas', '🏆 Campeones del Mundo', '🥇 Ganadores de Gran Premio', '🏎️ Escuderías Asentadas (>50 GPs)', '🔧 Equipos Fugaces (<50 GPs)']
    cat_sel = st.sidebar.selectbox("1. Nivel de Éxito Histórico:", categorias, key='filtro_cat_eq')
    
    df_sidebar = df_f1.copy()
    if st.session_state['filtro_cat_eq'] != 'Todas':
        df_sidebar = df_sidebar[df_sidebar['categoria_exito'] == st.session_state['filtro_cat_eq']]
        
    decadas_disp = sorted(df_sidebar['decada_str'].dropna().unique())
    decada_sel = st.sidebar.selectbox("2. Década de Debut:", ['Todas'] + decadas_disp, key='filtro_dec_eq')
    if st.session_state['filtro_dec_eq'] != 'Todas':
        df_sidebar = df_sidebar[df_sidebar['decada_str'] == st.session_state['filtro_dec_eq']]
        
    estado_sel = st.sidebar.radio("3. Estado Profesional:", ['Todos', 'Actual', 'Inactiva'], key='filtro_est_eq')
    if st.session_state['filtro_est_eq'] != 'Todos':
        df_sidebar = df_sidebar[df_sidebar['estado_equipo'] == st.session_state['filtro_est_eq']]
        
    equipos_disponibles = sorted(df_sidebar['constructor_name'].dropna().unique())
    
    if equipos_disponibles:
        eq_actual = st.session_state.get('selector_equipo', '')
        if eq_actual not in equipos_disponibles:
            favoritos = ["Ferrari", "McLaren", "Red Bull", "Mercedes", "Williams"]
            encontrado = False
            for fav in favoritos:
                if fav in equipos_disponibles:
                    st.session_state['selector_equipo'] = fav
                    encontrado = True
                    break
            if not encontrado and equipos_disponibles:
                st.session_state['selector_equipo'] = equipos_disponibles[0]
                
        equipo_sel = st.sidebar.selectbox("4. Selecciona la Escudería:", equipos_disponibles, key='selector_equipo')
    else:
        st.sidebar.warning("No hay escuderías con esos filtros.")
        equipo_sel = None

    if equipo_sel:
        df_eq = df_f1[df_f1['constructor_name'] == equipo_sel].sort_values('race_date')
        color_oficial = obtener_color_escuderia(equipo_sel)
        
        st.divider()
        col_img, col_info = st.columns([1, 2.5])
        
        with col_img:
            img_url = obtener_imagen_wikipedia(equipo_sel)
            if img_url:
                st.markdown(f"""
                <div style="border-radius: 10px; overflow: hidden; width: 100%; height: 160px; box-shadow: 0px 4px 8px rgba(0,0,0,0.3); border: 2px solid {color_oficial}; background-color: white; display: flex; align-items: center; justify-content: center;">
                    <img src="{img_url}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
                </div>
                """, unsafe_allow_html=True)
            else:
                inicial = equipo_sel[0].upper()
                st.markdown(f"""
                <div style="background-color: {color_oficial}; border-radius: 10px; width: 100%; height: 160px; display: flex; align-items: center; justify-content: center; box-shadow: 0px 4px 8px rgba(0,0,0,0.3);">
                    <span style="color: white; font-size: 80px; font-weight: bold; font-family: sans-serif;">{inicial}</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col_info:
            estado = df_eq['estado_equipo'].iloc[0]
            badge = "green" if estado == "Actual" else "gray"
            periodos_actividad = calcular_etapas_activas(df_eq['season'])
            
            st.subheader(f"🏭 {equipo_sel}")
            st.markdown(f"**Estado:** :{badge}[{estado}]")
            st.markdown(f"*Período(s) en activo:* **{periodos_actividad}**")

        st.markdown("<br>", unsafe_allow_html=True)
        
        total_carreras = df_eq.groupby(['season', 'round_number']).ngroups
        victorias = len(df_eq[df_eq['finish_position_num'] == 1])
        puntos = df_eq['points'].sum()
        
        puntos_anuales_equipos = df_f1[df_f1['season'] >= 1958].groupby(['season', 'constructor_name'])['points'].sum().reset_index()
        if not puntos_anuales_equipos.empty:
            idx_camp_eq = puntos_anuales_equipos.groupby('season')['points'].idxmax()
            campeones_eq = puntos_anuales_equipos.loc[idx_camp_eq]['constructor_name'].tolist()
            mundiales_eq = campeones_eq.count(equipo_sel)
        else:
            mundiales_eq = 0
            
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🏆 Mundiales (desde 1958)", mundiales_eq)
        c2.metric("🥇 Victorias totales", victorias)
        c3.metric("🏎️ Grandes premios", total_carreras)
        c4.metric("📊 Puntos históricos", f"{puntos:,.1f}".replace(",", "."))

        st.divider()
        st.subheader("🗺️ Huella Global de Victorias")
        st.markdown(f"*Este mapa de calor ilustra el éxito internacional de la escudería. Cuanto más intenso es el color de un país, más carreras ha ganado **{equipo_sel}** en ese territorio.*")
        
        df_victorias_map = df_eq[df_eq['finish_position_num'] == 1].copy()
        
        if not df_victorias_map.empty:
            mapa_datos = df_victorias_map.groupby(['country_eng', 'country_es']).size().reset_index(name='Victorias')
            
            fig_mapa = px.choropleth(
                mapa_datos,
                locations="country_eng", locationmode="country names",
                color="Victorias", hover_name="country_es",
                color_continuous_scale=[[0, 'rgba(255,255,255,0.1)'], [1, color_oficial]],
                projection="natural earth"
            )
            
            fig_mapa.update_geos(
                showcountries=True, countrycolor="rgba(128,128,128,0.3)",
                showcoastlines=True, coastlinecolor="rgba(128,128,128,0.3)",
                showland=True, landcolor="rgba(200,200,200,0.1)",
                fitbounds="locations"
            )
            fig_mapa.update_layout(margin=dict(r=0, t=0, l=0, b=0), height=450, paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.info(f"El equipo {equipo_sel} no ha registrado victorias oficiales para generar el mapa de dominio territorial.")

        st.divider()
        st.subheader("📈 Trayectoria y eras de éxito")
        
        col_linea, col_fiabilidad = st.columns([1.5, 1])
        
        with col_linea:
            st.markdown("**Evolución de puntos por temporada**")
            st.markdown("*Observa los picos de rendimiento que marcan las épocas doradas del equipo. Las caídas a cero indican periodos en los que la escudería no participó en el mundial.*")
            
            pts_temporada = df_eq.groupby('season')['points'].sum().reset_index()
            min_y = int(pts_temporada['season'].min())
            max_y = int(pts_temporada['season'].max())
            todas_temporadas = pd.DataFrame({'season': range(min_y, max_y + 1)})
            pts_temporada = todas_temporadas.merge(pts_temporada, on='season', how='left').fillna(0)
            
            fig_era = px.area(pts_temporada, x='season', y='points', color_discrete_sequence=[color_oficial],
                              labels={'season': 'Año', 'points': 'Puntos Totales'})
            fig_era.update_layout(height=350, margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig_era, use_container_width=True)
            
        with col_fiabilidad:
            st.markdown("**Fiabilidad del monoplaza**")
            st.markdown("*Un coche rápido también debe llegar a la meta. Esta gráfica desglosa los motivos por los que el equipo no ha logrado terminar las carreras, diferenciando entre averías mecánicas y accidentes.*")
            
            def clasificar_fiabilidad(row):
                if not pd.isna(row['finish_position_num']): return 'Clasificado / Terminó'
                
                if 'status' in row and pd.notna(row['status']):
                    status_str = str(row['status']).lower()
                    if any(x in status_str for x in ['accident', 'collision', 'spun', 'crash']):
                        return 'Abandono por accidente'
                    elif any(x in status_str for x in ['engine', 'gearbox', 'brakes', 'hydraulics', 'electrical', 'suspension', 'mechanical', 'overheating']):
                        return 'Abandono mecánico (Avería)'
                    else:
                        return 'Otro tipo de DNF'
                else:
                    return 'Abandono (avería / accidente)'
            
            df_eq['tipo_fin'] = df_eq.apply(clasificar_fiabilidad, axis=1)
            dist_fiabilidad = df_eq['tipo_fin'].value_counts().reset_index()
            
            fig_donut = px.pie(
                dist_fiabilidad, values='count', names='tipo_fin', hole=0.5,
                color='tipo_fin',
                color_discrete_map={
                    'Clasificado / Terminó': '#00C853',           
                    'Abandono mecánico (avería)': '#FF9100',      
                    'Abandono por accidente': '#FF1744',          
                    'Otro tipo de DNF': '#9E9E9E',
                    'Abandono (avería / accidente)': '#FF5252'    
                }
            )
            fig_donut.update_traces(textposition='inside', textinfo='percent')
            fig_donut.update_layout(height=350, margin=dict(t=10, b=10, l=0, r=0), showlegend=True, legend=dict(yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
            st.plotly_chart(fig_donut, use_container_width=True)

        st.divider()
        st.subheader(f"🎖️ Pilotos históricos de {equipo_sel}")
        st.markdown("*Explora la lista de pilotos que han competido para este equipo, ordenados por el número de Grandes Premios disputados.*")
        
        salon_fama = df_eq.groupby('driver_name').agg(
            Años_Activo=('season', lambda x: calcular_etapas_activas(x)),
            Carreras=('round_number', 'count'),
            Victorias=('finish_position_num', lambda x: (x == 1).sum()),
            Puntos_Aportados=('points', 'sum')
        ).reset_index().sort_values('Carreras', ascending=False)
        
        salon_fama.columns = ['Piloto', 'Período(s)', 'GPs Disputados', 'Victorias', 'Puntos Aportados']
        st.dataframe(salon_fama, hide_index=True, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("🔗 **¿Te gustaría explorar la trayectoria de alguno de estos pilotos en detalle?**")
        
        col_sel_p, col_btn_p = st.columns([2, 1])
        with col_sel_p:
            piloto_viaje = st.selectbox("Selecciona un piloto del equipo para ir a su perfil:", salon_fama['Piloto'])
        with col_btn_p:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button(f"Ir a la ficha de {piloto_viaje} ➔", use_container_width=True):
                # Guardamos el piloto en la memoria de la aplicación
                st.session_state['piloto_externo'] = piloto_viaje
                
                try:
                    paginas = os.listdir("pages")
                    archivo_pilotos = next((p for p in paginas if "pilotos" in p.lower() and p.endswith(".py")), None)
                    if archivo_pilotos:
                        st.switch_page(f"pages/{archivo_pilotos}")
                    else:
                        st.error("⚠️ No se ha encontrado el archivo de la página de pilotos.")
                except Exception as e:
                    st.error(f"Error en la navegación: {e}")

except FileNotFoundError:
    st.error("⚠️ Archivo 'f1_race_results_1950_2025.csv' no encontrado en la carpeta 'datos/'.")