
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("🎶 Análisis de Hábitos Musicales con Spotify Data")
st.markdown("---")

# --- 1. CARGA DE DATOS ---
st.header("1. Carga de Datos")
DATA_PATH = 'datos_canciones.csv'

@st.cache_data
def load_data(path):
    try:
        df = pd.read_csv(path)
        df['played_at'] = pd.to_datetime(df['played_at'])
        df.dropna(subset=['Song_Name', 'Artist_name'], inplace=True)
        df['Song_Name'] = df['Song_Name'].str.title()
        df['Artist_name'] = df['Artist_name'].str.title()
        return df
    except FileNotFoundError:
        st.error(f"Error: El archivo '{path}' no se encontró. Asegúrate de que existe en el mismo directorio.")
        return pd.DataFrame()

df = load_data(DATA_PATH)

if not df.empty:
    st.success(f"Datos cargados exitosamente desde '{DATA_PATH}'. {len(df)} registros encontrados.")
    st.dataframe(df.head())
else:
    st.warning("No se pudo cargar el archivo de datos. Por favor, verifica la ruta y el nombre del archivo.")

st.markdown("---")

# --- 2. CANCIÓN MÁS ESCUCHADA ---
st.header("2. Canción Más Escuchada")

if not df.empty:
    fav_song_counts = df.groupby(["Song_Name"])["Song_ID"].count()
    if not fav_song_counts.empty:
        most_listened_song = fav_song_counts.idxmax()
        most_listened_song_count = fav_song_counts.max()

        st.markdown(f"La **canción más escuchada** es: <span style='color: #1DB954; font-size: 24px; font-weight: bold;'>{most_listened_song}</span> con **{most_listened_song_count}** reproducciones.", unsafe_allow_html=True)

        artists_for_most_listened = df[df['Song_Name'] == most_listened_song]['Artist_name'].unique()
        if artists_for_most_listened.size > 0:
            st.write(f"Artista(s) de esta canción: **{', '.join(artists_for_most_listened)}**")
        else:
            st.write("No se encontraron artistas para esta canción.")
    else:
        st.warning("No hay datos de canciones para calcular la más escuchada.")
else:
    st.info("Carga de datos necesaria para esta sección.")

st.markdown("---")

# --- 3. MOMENTO MÁS PROBABLE DE ESCUCHA ---
st.header("3. Momento Más Probable de Escucha")

if not df.empty and not fav_song_counts.empty:
    # Filtramos el historial solo para la canción más escuchada
    df_top_cancion = df[df['Song_Name'] == most_listened_song]
    
    # Extraemos las horas y minutos de reproducción de esa canción
    horas = df_top_cancion['played_at'].dt.hour
    minutos = df_top_cancion['played_at'].dt.minute
    
    # Calculamos el promedio de tiempo aproximado
    hora_promedio = int(horas.mean())
    minuto_promedio = int(minutos.mean())
    
    # Damos formato de reloj HH:MM
    hora_estimada = f"{hora_promedio:02d}:{minuto_promedio:02d}"
    
    # Mostramos la predicción directa
    st.markdown(
        f"Basado en tus hábitos, el aproximado de la hora en la que escucharás **{most_listened_song}** "
        f"es a las <span style='color: #1DB954; font-size: 22px; font-weight: bold;'>{hora_estimada}</span>.", 
        unsafe_allow_html=True
    )
else:
    st.info("Carga de datos necesaria para esta sección.")

st.markdown("---")
st.caption("© 2024 Análisis de Hábitos Musicales - Creado con Streamlit")
