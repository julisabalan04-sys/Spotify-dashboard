
import streamlit as st
import pandas as pd
import requests  # Librería para consultar la API de letras

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
            artista_principal = artists_for_most_listened[0]
            st.write(f"Artista(s) de esta canción: **{', '.join(artists_for_most_listened)}**")
        else:
            artista_principal = None
            st.write("No se encontraron artistas para esta canción.")
    else:
        st.warning("No hay datos de canciones para calcular la más escuchada.")
else:
    st.info("Carga de datos necesaria para esta sección.")

st.markdown("---")

# --- 3. MOMENTO MÁS PROBABLE DE ESCUCHA ---
st.header("3. Momento Más Probable de Escucha")

if not df.empty and not fav_song_counts.empty:
    df_top_cancion = df[df['Song_Name'] == most_listened_song]
    horas = df_top_cancion['played_at'].dt.hour
    minutos = df_top_cancion['played_at'].dt.minute
    
    hora_promedio = int(horas.mean())
    minuto_promedio = int(minutos.mean())
    hora_estimada = f"{hora_promedio:02d}:{minuto_promedio:02d}"
    
    st.markdown(
        f"Basado en tus hábitos, el aproximado de la hora en la que escucharás **{most_listened_song}** "
        f"es a las <span style='color: #1DB954; font-size: 22px; font-weight: bold;'>{hora_estimada}</span>.", 
        unsafe_allow_html=True
    )
else:
    st.info("Carga de datos necesaria para esta sección.")

st.markdown("---")

# --- 4. PREDICCIÓN DE EMOCIÓN (EXTRACCIÓN REAL) ---
st.header("4. Análisis de Emoción Basado en la Letra")

if not df.empty and artista_principal and most_listened_song:
    st.write(f"Buscando la letra de *{most_listened_song}* de *{artista_principal}*...")
    
    # Llamamos a la API gratuita de letras
    url_api = f"https://api.lyrics.ovh/v1/{artista_principal}/{most_listened_song}"
    
    try:
        respuesta = requests.get(url_api, timeout=10)
        
        if respuesta.status_code == 200:
            datos_letra = respuesta.json()
            letra_texto = datos_letra.get("lyrics", "")
            
            if letra_texto:
                # 1. Mostrar fragmento de la letra de forma estética
                with st.expander("Ver letra de la canción encontrada"):
                    st.text(letra_texto)
                
                # 2. Análisis Lógico de Emociones (Modelo Simple por palabras clave)
                letra_minuscula = letra_texto.lower()
                
                palabras_alegria = ['amor', 'alegría', 'gracia', 'santo', 'gozo', 'cantar', 'luz', 'viva', 'fiesta', 'feliz']
                palabras_tristeza = ['llorar', 'triste', 'dolor', 'soledad', 'vacío', 'adiós', 'quebrantado', 'perdí']
                palabras_paz = ['paz', 'calma', 'amado', 'espera', 'confío', 'reposo', 'descanso', 'fiel']
                
                puntos_alegria = sum(letra_minuscula.count(p) for p in palabras_alegria)
                puntos_tristeza = sum(letra_minuscula.count(p) for p in palabras_tristeza)
                puntos_paz = sum(letra_minuscula.count(p) for p in palabras_paz)
                
                # Determinar la emoción predominante
                if puntos_paz >= puntos_alegria and puntos_paz >= puntos_tristeza:
                    emocion = "Calma / Paz Espiritual 🕊️"
                    color_emocion = "#4A90E2"  # Azul
                elif puntos_alegria >= puntos_tristeza:
                    emocion = "Alegría / Exaltación 🎉"
                    color_emocion = "#1DB954"  # Verde Spotify
                else:
                    emocion = "Melancolía / Nostalgia 😢"
                    color_emocion = "#E0B0FF"  # Lila
                
                st.markdown(
                    f"El análisis de procesamiento de texto indica que la emoción predominante de esta canción es: "
                    f"<span style='color: {color_emocion}; font-size: 24px; font-weight: bold;'>{emocion}</span>.", 
                    unsafe_allow_html=True
                )
            else:
                st.warning("La API respondió, pero el texto de la letra estaba vacío.")
        else:
            # Si no encuentra la letra exacta (muy común con música cristiana o artistas locales en bases de datos globales)
            st.warning("No se encontró la letra exacta en la base de datos pública de internet.")
            st.info("💡 **Predicción Simulada:** Dado que el artista es de género espiritual/gospel (*Montesanto*), la emoción estimada por defecto es **Inspiracional / Devocional ✨**.")
            
    except Exception as e:
        st.error("Hubo un problema al conectar con el servidor de letras.")
else:
    st.info("Carga de datos necesaria para esta sección.")

st.markdown("---")
st.caption("© 2024 Análisis de Hábitos Musicales - Creado con Streamlit")
