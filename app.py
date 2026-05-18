
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🎶 Análisis de Hábitos Musicales con Spotify Data")
st.markdown("---")

# --- Cargar Datos ---
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

# --- Canción Más Escuchada ---
st.header("2. Canción Más Escuchada")

most_listened_song = None # Initialize
fav_song_counts = pd.Series() # Initialize as empty Series

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

# --- Momento Más Probable de Escucha para la Canción Más Escuchada ---
st.header("3. Momento Más Probable de Escucha")

if most_listened_song:
    df_most_listened = df[df['Song_Name'] == most_listened_song].copy()
    df_most_listened['hour_of_day'] = df_most_listened['played_at'].dt.hour
    
    hourly_counts = df_most_listened['hour_of_day'].value_counts().sort_index()
    
    if not hourly_counts.empty:
        most_frequent_hour = hourly_counts.idxmax()
        st.markdown(f"La hora más frecuente en la que escuchas '**{most_listened_song}**' es a las <span style='color: #1DB954; font-size: 24px; font-weight: bold;'>{most_frequent_hour:02d}:00</span>.", unsafe_allow_html=True)

        df_hourly_plot = pd.DataFrame({
            'Hora del Día': hourly_counts.index.astype(str) + ':00',
            'Reproducciones': hourly_counts.values
        })
        
        fig = px.bar(
            df_hourly_plot,
            x='Hora del Día',
            y='Reproducciones',
            color='Reproducciones',
            title=f'Frecuencia de Reproducción de "{most_listened_song}" por Hora del Día',
            text='Reproducciones'
        )
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No hay suficientes datos para determinar el patrón de escucha horario de '{most_listened_song}'.")
else:
    st.info("Identifica la canción más escuchada para analizar sus patrones horarios.")

st.markdown("---")

# --- Predicción de Emoción (Explicación) ---
st.header("4. Predicción de Emoción para la Canción Más Escuchada")

if not df.empty and not fav_song_counts.empty:
    st.markdown(f"Para predecir el tipo de emoción asociada a la canción '**{most_listened_song}**' de manera precisa, se necesitarían los siguientes elementos:")
    st.markdown("""
    *   **Datos Adicionales**: El análisis de emoción generalmente se basa en el contenido textual, como las **letras de la canción**. Nuestros datos actuales no incluyen esta información.
    *   **Modelo de Procesamiento de Lenguaje Natural (NLP)**: Se requiere un modelo entrenado específicamente para clasificar textos en diferentes categorías de emoción (ej. alegría, tristeza, enojo, calma).
    *   **Integración de API de NLP/Sentimiento**: Alternativamente, se podrían utilizar servicios de terceros (APIs) que ofrezcan análisis de sentimiento o emoción a partir de textos.

    **Con los datos disponibles actualmente (solo nombre de canción, artista, etc.), no es posible realizar una predicción de emoción precisa.** El nombre de una canción por sí solo rara vez es un indicador fiable de su emoción.
    """)
    st.info("**Sugerencia:** Si deseas implementar la predicción de emoción, primero necesitarías obtener las letras de las canciones y luego integrar un modelo o una API de NLP.")
else:
    st.info("Carga de datos necesaria para esta sección.")

st.markdown("---")
st.caption("© 2024 Análisis de Hábitos Musicales - Creado con Streamlit")
