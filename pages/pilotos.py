import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import hashlib
import requests
import folium
from streamlit_folium import st_folium

st.title("🏎️ Pilotos de F1")
st.markdown("""
**Bienvenido al módulo de exploración de pilotos.**

Esta sección es un espacio dedicado a repasar la trayectoria de los protagonistas que han escrito la historia de la Fórmula 1. Aquí podrás reconstruir la carrera de cualquier piloto, observar cómo ha evolucionado su trayectoria pasando por distintas escuderías, analizar su rendimiento temporada a temporada y localizar en un mapa mundial aquellos circuitos donde han logrado sus mayores éxitos.
""")

#Css para ajustar nombres que no aparecen correctamente
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

# Llamada a la api de la wikipedia para recuperar imagenes de los pilotos
@st.cache_data(show_spinner=False)
def obtener_imagen_wikipedia(nombre_piloto):
    headers = {"User-Agent": "F1DashboardApp/1.0"}
    url_search_es = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={nombre_piloto} piloto&utf8=&format=json"
    try:
        res = requests.get(url_search_es, headers=headers, timeout=3).json()
        if res['query']['search']:
            titulo_exacto = res['query']['search'][0]['title']
            url_img = f"https://es.wikipedia.org/w/api.php?action=query&titles={titulo_exacto}&prop=pageimages&format=json&pithumbsize=400"
            res_img = requests.get(url_img, headers=headers, timeout=3).json()
            pages = res_img['query']['pages']
            for page_id in pages:
                if 'thumbnail' in pages[page_id]: return pages[page_id]['thumbnail']['source']
    except: pass
    
    url_search_en = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={nombre_piloto} racing driver&utf8=&format=json"
    try:
        res = requests.get(url_search_en, headers=headers, timeout=3).json()
        if res['query']['search']:
            titulo_exacto = res['query']['search'][0]['title']
            url_img = f"https://en.wikipedia.org/w/api.php?action=query&titles={titulo_exacto}&prop=pageimages&format=json&pithumbsize=400"
            res_img = requests.get(url_img, headers=headers, timeout=3).json()
            pages = res_img['query']['pages']
            for page_id in pages:
                if 'thumbnail' in pages[page_id]: return pages[page_id]['thumbnail']['source']
    except: pass
    
    return None

@st.cache_data
def cargar_datos_pilotos():
    ruta_datos = "datos/"
    df = pd.read_csv(os.path.join(ruta_datos, "f1_race_results_1950_2025.csv"))
    
    df['driver_nationality'] = df['driver_nationality'].astype(str).str.strip().str.title()
    df['circuit_country'] = df['circuit_country'].astype(str).str.strip().str.title()
    
    mapeo_nacionalidades = {
        'Austria': 'Austriaco', 'Belgium': 'Belga', 'Brazil': 'Brasileño', 'Canada': 'Canadiense',
        'Chile': 'Chileno', 'China': 'Chino', 'Colombia': 'Colombiano', 'Czechia': 'Checo',
        'Czech Republic': 'Checo', 'Denmark': 'Danés', 'Finland': 'Finlandés', 'France': 'Francés',
        'Germany': 'Alemán', 'Great Britain': 'Británico', 'United Kingdom': 'Británico', 'Uk': 'Británico',
        'Hungary': 'Húngaro', 'India': 'Indio', 'Indonesia': 'Indonesio', 'Ireland': 'Irlandés',
        'Italy': 'Italiano', 'Japan': 'Japonés', 'Malaysia': 'Malasio', 'Mexico': 'Mexicano',
        'Netherlands': 'Neerlandés', 'New Zealand': 'Neozelandés', 'Poland': 'Polaco', 'Portugal': 'Portugués',
        'Russia': 'Ruso', 'South Africa': 'Sudafricano', 'Spain': 'Español', 'Sweden': 'Sueco',
        'Switzerland': 'Suizo', 'Thailand': 'Tailandés', 'Uruguay': 'Uruguayo', 'Usa': 'Estadounidense',
        'United States': 'Estadounidense', 'Venezuela': 'Venezolano', 'Argentina': 'Argentino', 'Monaco': 'Monegasco',
        'British': 'Británico', 'German': 'Alemán', 'Spanish': 'Español', 'French': 'Francés',
        'Italian': 'Italiano', 'Brazilian': 'Brasileño', 'Argentine': 'Argentino', 'Argentinian': 'Argentino',
        'Austrian': 'Austriaco', 'Australian': 'Australiano', 'Canadian': 'Canadiense', 'Japanese': 'Japonés', 
        'Dutch': 'Neerlandés', 'Finnish': 'Finlandés', 'Mexican': 'Mexicano', 'Monegasque': 'Monegasco', 
        'Belgian': 'Belga', 'American': 'Estadounidense', 'Swiss': 'Suizo', 'Swedish': 'Sueco', 
        'New Zealander': 'Neozelandés', 'South African': 'Sudafricano', 'Colombian': 'Colombiano', 
        'Russian': 'Ruso', 'Polish': 'Polaco', 'Venezuelan': 'Venezolano', 'Danish': 'Danés', 
        'Thai': 'Tailandés', 'Chinese': 'Chino', 'Indian': 'Indio', 'Portuguese': 'Portugués', 
        'Irish': 'Irlandés', 'Chilean': 'Chileno', 'Uruguayan': 'Uruguayo', 'Czech': 'Checo', 
        'Malaysian': 'Malasio', 'Hungarian': 'Húngaro', 'Indonesian': 'Indonesio'
    }
    df['driver_nationality'] = df['driver_nationality'].replace(mapeo_nacionalidades)
    
    df['country'] = df['circuit_country'].str.replace('-', ' ')
    mapeo_paises_es = {
        'Spain': 'España', 'Uk': 'Reino Unido', 'Great Britain': 'Reino Unido', 'Germany': 'Alemania', 
        'France': 'Francia', 'Italy': 'Italia', 'Brazil': 'Brasil', 'Argentina': 'Argentina', 
        'Austria': 'Austria', 'Australia': 'Australia', 'Canada': 'Canadá', 'Japan': 'Japón', 
        'Netherlands': 'Países Bajos', 'Mexico': 'México', 'Monaco': 'Mónaco', 'Belgium': 'Bélgica', 
        'United States Of America': 'Estados Unidos', 'United States': 'Estados Unidos', 'Switzerland': 'Suiza', 
        'Sweden': 'Suecia', 'South Africa': 'Sudáfrica', 'China': 'China', 'Russia': 'Rusia', 'India': 'India', 
        'Portugal': 'Portugal', 'Malaysia': 'Malasia', 'Hungary': 'Hungría', 'Finland': 'Finlandia',
        'Bahrain': 'Bahréin', 'Saudi Arabia': 'Arabia Saudita', 'Uae': 'Abu Dabi', 
        'United Arab Emirates': 'Abu Dabi', 'Singapore': 'Singapur', 'Azerbaijan': 'Azerbaiyán',
        'Qatar': 'Catar', 'Turkey': 'Turquía', 'South Korea': 'Corea del Sur', 'Morocco': 'Marruecos'
    }
    df['country'] = df['country'].replace(mapeo_paises_es)
    
    mapeo_nacionalidad_a_pais = {
        'Español': 'España', 'Británico': 'Reino Unido', 'Alemán': 'Alemania', 'Francés': 'Francia',
        'Italiano': 'Italia', 'Brasileño': 'Brasil', 'Argentino': 'Argentina', 'Austriaco': 'Austria',
        'Australiano': 'Australia', 'Canadiense': 'Canadá', 'Japonés': 'Japón', 'Neerlandés': 'Países Bajos',
        'Finlandés': 'Finlandia', 'Mexicano': 'México', 'Monegasco': 'Mónaco', 'Belga': 'Bélgica',
        'Estadounidense': 'Estados Unidos', 'Suizo': 'Suiza', 'Sueco': 'Suecia', 'Sudafricano': 'Sudáfrica',
        'Ruso': 'Rusia', 'Indio': 'India', 'Portugués': 'Portugal', 'Chino': 'China', 'Malasio': 'Malasia',
        'Chileno': 'Chile', 'Colombiano': 'Colombia', 'Checo': 'Chequia', 'Uruguayo': 'Uruguay',
        'Venezolano': 'Venezuela', 'Danés': 'Dinamarca', 'Tailandés': 'Tailandia', 'Polaco': 'Polonia',
        'Indonesio': 'Indonesia', 'Irlandés': 'Irlanda', 'Neozelandés': 'Nueva Zelanda'
    }
    df['driver_home_country'] = df['driver_nationality'].map(mapeo_nacionalidad_a_pais)
    
    df['race_date'] = pd.to_datetime(df['race_date'], errors='coerce')
    df['grid_position'] = pd.to_numeric(df['grid_position'], errors='coerce')
    df['finish_position_num'] = pd.to_numeric(df['finish_position_num'], errors='coerce')
    
    ultima_temp_global = df['season'].max()
    pilotos_activos = df[df['season'] >= (ultima_temp_global - 1)]['driver_name'].unique()
    df['status'] = df['driver_name'].apply(lambda x: 'En Activo' if x in pilotos_activos else 'Retirado')
    
    return df

try:
    df_f1 = cargar_datos_pilotos()

    st.sidebar.header("⚙️ Filtros de Búsqueda")
    
    if 'piloto_externo' in st.session_state:
        st.session_state['filtro_nac_piloto'] = 'Todas'
        st.session_state['filtro_est_piloto'] = 'Todos'
        st.session_state['selector_piloto'] = st.session_state['piloto_externo']
        del st.session_state['piloto_externo'] 

    if 'filtro_nac_piloto' not in st.session_state:
        st.session_state['filtro_nac_piloto'] = 'Todas'
    if 'filtro_est_piloto' not in st.session_state:
        st.session_state['filtro_est_piloto'] = 'Todos'

    nacionalidades = sorted(df_f1['driver_nationality'].dropna().unique())
    nacionalidad_sel = st.sidebar.selectbox("1. Nacionalidad del Piloto:", ['Todas'] + nacionalidades, key='filtro_nac_piloto')
    
    estado_sel = st.sidebar.radio("2. Estado Profesional:", ['Todos', 'En Activo', 'Retirado'], horizontal=True, key='filtro_est_piloto')
    
    df_filtro_sidebar = df_f1.copy()
    if st.session_state['filtro_nac_piloto'] != 'Todas':
        df_filtro_sidebar = df_filtro_sidebar[df_filtro_sidebar['driver_nationality'] == st.session_state['filtro_nac_piloto']]
    if st.session_state['filtro_est_piloto'] != 'Todos':
        df_filtro_sidebar = df_filtro_sidebar[df_filtro_sidebar['status'] == st.session_state['filtro_est_piloto']]
    
    pilotos_disponibles = sorted(df_filtro_sidebar['driver_name'].dropna().unique())
    
    if pilotos_disponibles:
        piloto_actual = st.session_state.get('selector_piloto', '')
        if piloto_actual not in pilotos_disponibles:
            favoritos = ["Fernando Alonso", "Carlos Sainz", "Lewis Hamilton", "Michael Schumacher", "Ayrton Senna"]
            encontrado = False
            for fav in favoritos:
                if fav in pilotos_disponibles:
                    st.session_state['selector_piloto'] = fav
                    encontrado = True
                    break
            if not encontrado and pilotos_disponibles:
                st.session_state['selector_piloto'] = pilotos_disponibles[0]
                
        piloto_sel = st.sidebar.selectbox("3. Selecciona el Piloto:", pilotos_disponibles, key='selector_piloto')
    else:
        st.sidebar.warning("No hay pilotos que cumplan los filtros seleccionados.")
        piloto_sel = None

    if piloto_sel:
        df_piloto = df_f1[df_f1['driver_name'] == piloto_sel].sort_values('race_date')
        
        st.divider()
        col_avatar, col_bio = st.columns([1, 2.5])
        
        with col_avatar:
            imagen_url = obtener_imagen_wikipedia(piloto_sel)
            if imagen_url:
                st.markdown(f"""
                <div style="border-radius: 15px; overflow: hidden; width: 140px; height: 140px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3); border: 3px solid white;">
                    <img src="{imagen_url}" style="width: 100%; height: 100%; object-fit: cover;">
                </div>
                """, unsafe_allow_html=True)
            else:
                iniciales = "".join([p[0] for p in piloto_sel.split()[:2]])
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1E88E5 0%, #0D47A1 100%);
                                border-radius: 15px; width: 140px; height: 140px; 
                                display: flex; align-items: center; justify-content: center;
                                box-shadow: 0px 4px 10px rgba(0,0,0,0.3); border: 3px solid white;">
                        <span style="color: white; font-size: 42px; font-weight: bold; font-family: sans-serif;">
                            {iniciales}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
            
        with col_bio:
            nac = df_piloto['driver_nationality'].iloc[0]
            status_piloto = df_piloto['status'].iloc[0]
            badge_color = "green" if status_piloto == "En Activo" else "gray"
            
            st.subheader(f"📊 Trayectoria de {piloto_sel}")
            st.markdown(f"**Nacionalidad:** {nac} | **Estado:** :{badge_color}[{status_piloto}]")
            st.markdown(f"*Su andadura en la máxima categoría comenzó en el año **{df_piloto['season'].min()}**, compitiendo en el Gran Premio de {df_piloto['country'].iloc[0]}.*")

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        
        total_carreras = len(df_piloto.drop_duplicates(subset=['season', 'round_number']))
        victorias = len(df_piloto[df_piloto['finish_position_num'] == 1])
        puntos_totales = df_piloto['points'].sum()
        
        puntos_anuales_todos = df_f1.groupby(['season', 'driver_name'])['points'].sum().reset_index()
        idx_campeones = puntos_anuales_todos.groupby('season')['points'].idxmax()
        campeones_historicos = puntos_anuales_todos.loc[idx_campeones]['driver_name'].tolist()
        mundiales = campeones_historicos.count(piloto_sel)
        
        c1.metric("🏆 Mundiales", mundiales if mundiales > 0 else "0")
        c2.metric("🥇 Victorias", victorias)
        c3.metric("🏎️ GPs Disputados", total_carreras)
        c4.metric("🏁 Puntos Históricos", f"{puntos_totales:,.1f}".replace(",", "."))

        st.divider()
        st.subheader("🏁 Cronología de escuderías")
        st.markdown("*Esta línea temporal muestra la evolución profesional del piloto. Los bloques de color representan las etapas en cada equipo, permitiéndote identificar fácilmente los cambios de escudería y sus etapas de mayor éxito.*")
        df_trayectoria = df_piloto.sort_values('race_date').copy()
        df_trayectoria['team_spell'] = (df_trayectoria['constructor_name'] != df_trayectoria['constructor_name'].shift()).cumsum()
        
        trayectoria_etapas = df_trayectoria.groupby(['team_spell', 'constructor_name']).agg(
            Año_Inicio=('season', 'min'), Año_Fin=('season', 'max'),
            Fecha_Inicio=('race_date', 'min'), Fecha_Fin=('race_date', 'max'),
            Carreras=('round_number', 'count'),
            Victorias=('finish_position_num', lambda x: (x == 1).sum())
        ).reset_index().sort_values('Año_Inicio')
        
        trayectoria_etapas['Periodo'] = trayectoria_etapas.apply(
            lambda r: f"{r['Año_Inicio']} - {r['Año_Fin']}" if r['Año_Inicio'] != r['Año_Fin'] else str(r['Año_Inicio']), axis=1
        )
        trayectoria_etapas['Fecha_Fin'] = trayectoria_etapas['Fecha_Fin'] + pd.Timedelta(days=15)
        
        col_tabla_t, col_gantt = st.columns([1.2, 1])
        with col_tabla_t:
            st.dataframe(trayectoria_etapas[['constructor_name', 'Periodo', 'Carreras', 'Victorias']].rename(columns={'constructor_name': 'Escudería'}), hide_index=True, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("🔗 **¿Quieres ver la historia de alguna de estas escuderías?**")
            
            col_sel_e, col_btn_e = st.columns([2, 1])
            with col_sel_e:
                escuderia_viaje = st.selectbox("Selecciona una escudería para ir a su perfil:", trayectoria_etapas['constructor_name'].unique())
            with col_btn_e:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button(f"Ir a la ficha de {escuderia_viaje} ➔", use_container_width=True):
                    st.session_state['escuderia_externa'] = escuderia_viaje
                    try:
                        paginas = os.listdir("pages")
                        archivo_escuderias = next((p for p in paginas if "escuderia" in p.lower() and p.endswith(".py")), None)
                        if archivo_escuderias:
                            st.switch_page(f"pages/{archivo_escuderias}")
                        else:
                            st.error("⚠️ No se ha encontrado el archivo de la página de escuderías.")
                    except Exception as e:
                        st.error(f"Error en la navegación: {e}")
            
        with col_gantt:
            mapa_colores_gantt = {esc: obtener_color_escuderia(esc) for esc in trayectoria_etapas['constructor_name'].unique()}
            fig_gantt = px.timeline(
                trayectoria_etapas, x_start='Fecha_Inicio', x_end='Fecha_Fin', y='constructor_name',
                color='constructor_name', color_discrete_map=mapa_colores_gantt,
                labels={'constructor_name': 'Escudería'}
            )
            fig_gantt.update_yaxes(autorange="reversed")
            fig_gantt.update_layout(showlegend=False, height=300, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_gantt, use_container_width=True)

        

        st.divider()
        st.subheader("📅 Desglose por temporada")
        st.markdown("*¿Cómo fue realmente una temporada concreta para este piloto? Selecciona el año para explorar sus resultados detallados, su posición en parrilla y cómo se tradujo su esfuerzo en puntos en cada circuito.*")
        col_filt1, col_filt2 = st.columns([1, 2])
        
        with col_filt1:
            temporadas_piloto = sorted(df_piloto['season'].unique(), reverse=True)
            temp_sel = st.selectbox("Selecciona la temporada:", temporadas_piloto)
            
        df_temp = df_piloto[df_piloto['season'] == temp_sel].copy()
        
        with col_filt2:
            circuitos_temp = sorted(df_temp['circuit_name'].dropna().unique())
            circ_sel = st.multiselect("Filtrar por circuito:", circuitos_temp)

        if circ_sel:
            df_temp = df_temp[df_temp['circuit_name'].isin(circ_sel)]

        df_mundial = df_f1[df_f1['season'] == temp_sel].groupby('driver_name')['points'].sum().reset_index()
        df_mundial = df_mundial.sort_values(by='points', ascending=False).reset_index(drop=True)
        df_mundial['posicion'] = df_mundial.index + 1
        
        pos_mundial_arr = df_mundial[df_mundial['driver_name'] == piloto_sel]['posicion'].values
        pos_mundial_str = f"{pos_mundial_arr[0]}º" if len(pos_mundial_arr) > 0 else "N/A"
        
        equipos_temp = " / ".join(df_temp['constructor_name'].unique())
        pts_temp = df_temp['points'].sum()
        victorias_temp = len(df_temp[df_temp['finish_position_num'] == 1])
        
        c_k1, c_k2, c_k3, c_k4 = st.columns(4)
        c_k1.metric("🏆 Posición final", pos_mundial_str)
        c_k2.metric("🏎️ Escudería(s)", equipos_temp)
        c_k3.metric("📊 Puntos totales", f"{pts_temp:,.1f}".replace(",", "."))
        c_k4.metric("🥇 Victorias", victorias_temp)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        def estado_carrera(row):
            if pd.isna(row['finish_position_num']): return 'Retirado / DNF'
            return 'Clasificado'
            
        df_temp['Estado'] = df_temp.apply(estado_carrera, axis=1)
        df_temp['Gran Premio'] = "GP de " + df_temp['country']
        df_mostrar = df_temp[['round_number', 'Gran Premio', 'circuit_name', 'grid_position', 'finish_position_num', 'points', 'Estado']].copy()
        
        df_mostrar['grid_position'] = df_mostrar['grid_position'].fillna(-1).astype(int).astype(str).replace('-1', 'Pit Lane')
        df_mostrar['finish_position_num'] = df_mostrar['finish_position_num'].fillna(-1).astype(int).astype(str).replace('-1', '-')
        df_mostrar['points'] = df_mostrar['points'].fillna(0)
        
        df_mostrar = df_mostrar.rename(columns={
            'round_number': 'Ronda', 'circuit_name': 'Circuito', 'grid_position': 'Salida',
            'finish_position_num': 'Llegada', 'points': 'Puntos'
        }).sort_values('Ronda')
        
        st.dataframe(df_mostrar, hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("🗺️ Circuitos talismán")
        st.markdown(f"*¿Dónde ha brillado más? Este mapa destaca los 5 escenarios donde **{piloto_sel}** ha obtenido sus mejores resultados históricos, ya sean victorias, podios o sus clasificaciones más destacadas.*")
        
        df_clasificados = df_piloto[df_piloto['finish_position_num'].notna()].copy()
        
        if not df_clasificados.empty:
            df_clasificados['Es_Victoria'] = np.where(df_clasificados['finish_position_num'] == 1, 1, 0)
            df_clasificados['Es_Podio'] = np.where(df_clasificados['finish_position_num'] <= 3, 1, 0)
            df_clasificados['Es_Top10'] = np.where(df_clasificados['finish_position_num'] <= 10, 1, 0)
            
            talisman = df_clasificados.groupby('circuit_name').agg(
                Victorias=('Es_Victoria', 'sum'),
                Podios=('Es_Podio', 'sum'),
                Top10=('Es_Top10', 'sum'),
                Mejor_Posicion=('finish_position_num', 'min'),
                Lat=('circuit_latitude', 'first'),
                Lon=('circuit_longitude', 'first')
            ).reset_index()
            
            top_5 = talisman.sort_values(by=['Victorias', 'Podios', 'Top10', 'Mejor_Posicion'], ascending=[False, False, False, True]).head(5)
            
            with st.container():
                mapa_talisman = folium.Map(
                    location=[20, 0], zoom_start=2, min_zoom=1.5, max_bounds=True,
                    tiles='https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', 
                    attr='CartoDB Positron (No Labels)', min_lat=-85, max_lat=85, min_lon=-180, max_lon=180
                )
                
                for _, row in top_5.iterrows():
                    if row['Victorias'] > 0:
                        color_chincheta, icon_marker = "red", "trophy"
                    elif row['Podios'] > 0:
                        color_chincheta, icon_marker = "blue", "star"
                    else:
                        color_chincheta, icon_marker = "green", "check" # Para pilotos sin podios pero con buenos finales
                    
                    texto_tooltip = f"""
                    <div style='font-family: sans-serif; text-align: center;'>
                        <b>{row['circuit_name']}</b><br>
                        🏆 Victorias: {row['Victorias']}<br>
                        🍾 Podios Totales: {row['Podios']}<br>
                        🎯 Mejor Posición Histórica: {int(row['Mejor_Posicion'])}º
                    </div>
                    """
                    
                    folium.Marker(
                        location=[row['Lat'], row['Lon']],
                        tooltip=texto_tooltip,
                        icon=folium.Icon(color=color_chincheta, icon=icon_marker, prefix='fa')
                    ).add_to(mapa_talisman)
                
                st_folium(mapa_talisman, height=450, use_container_width=True, returned_objects=[])
        else:
            st.warning(f"⚠️ **{piloto_sel}** no ha logrado clasificar ni terminar ninguna carrera oficial en la F1.")

except FileNotFoundError:
    st.error("⚠️ Archivo 'f1_race_results_1950_2025.csv' no encontrado en la carpeta 'datos/'.")