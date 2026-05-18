import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import plotly.express as px
import pytz
import os

# --- 1. CONFIGURACIÓN DE CREDENCIALES DE SPOTIFY ---
# Pon aquí tus credenciales de Spotify para que la app funcione de forma independiente
CLIENT_ID = "46051393ce7c473384e5049f1572e543"
CLIENT_SECRET = "29c7d7910d0e4ce7bdfc59d473cb2bfb"

@st.cache_resource
def inicializar_spotify():
    try:
        auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        return spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        st.error(f"Error de autenticación con Spotify: {e}")
        return None

# Función para obtener características de audio de Spotify
def get_audio_features(track_id, sp_client):
    try:
        audio_features = sp_client.audio_features([track_id])[0]
        if audio_features:
            return {
                'danceability': audio_features.get('danceability'),
                'energy': audio_features.get('energy'),
                'valence': audio_features.get('valence'),
                'tempo': audio_features.get('tempo'),
                'acousticness': audio_features.get('acousticness'),
                'instrumentalness': audio_features.get('instrumentalness'),
                'liveness': audio_features.get('liveness'),
                'speechiness': audio_features.get('speechiness')
            }
        return None
    except Exception:
        return None

# Función para predecir la emoción basada en las características de audio
def predict_emotion(features):
    if not features:
        return "Desconocida"

    valence = features.get('valence', 0.5)
    energy = features.get('energy', 0.5)
    danceability = features.get('danceability', 0.5)

    if valence > 0.7 and energy > 0.7:
        return "Feliz y Energético 😄"
    elif valence > 0.5 and energy < 0.5:
        return "Calmado y Positivo 😊"
    elif valence < 0.3 and energy > 0.6:
        return "Enojado o Tenso 😠"
    elif valence < 0.3 and energy < 0.3:
        return "Triste o Reflexivo 😔"
    elif danceability > 0.7 and energy > 0.6:
        return "Animado y Bailable! 💃🕺"
    else:
        return "Neutral / Relajado 😌"

# --- Configuración y Layout de la Aplicación Streamlit ---
st.set_page_config(layout="wide", page_title="Predicción de Emociones Musicales")

st.title("🎵 App de Predicción de Emociones Musicales")
st.markdown("Esta aplicación predice el tipo de emoción de tus canciones escuchadas, analizando sus características de audio de Spotify y tendencias por hora/día.")

st.header("Tus Preferencias Musicales Recientes:")

# Archivo de datos que la app va a leer de forma independiente
csv_filename = "datos_canciones.csv"
sp = inicializar_spotify()

if os.path.exists(csv_filename) and sp is not None:
    # Cargar los datos desde el CSV
    df = pd.read_csv(csv_filename)
    
    # Asegurar que 'played_at' sea datetime y tenga la zona horaria correcta
    if not pd.api.types.is_datetime64_any_dtype(df['played_at']):
        df['played_at'] = pd.to_datetime(df['played_at'])
        mexico_tz = pytz.timezone('America/Mexico_City')
        # Si el datetime ya viene con localización, usamos tz_convert, si no, tz_localize
        try:
            df['played_at'] = df['played_at'].dt.tz_convert(mexico_tz)
        except TypeError:
            df['played_at'] = df['played_at'].dt.tz_localize('UTC').dt.tz_convert(mexico_tz)

    # Calcular hora y día de la semana para los análisis
    df['hour_of_day'] = df['played_at'].dt.hour
    df['day_of_week'] = df['played_at'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=day_order, ordered=True)

    # Obtener canciones únicas para no saturar la API de Spotify
    with st.spinner("Analizando las características de audio de tus canciones..."):
        unique_tracks = df[['Song_ID', 'Song_Name', 'Artist_name']].drop_duplicates(subset=['Song_ID']).copy()
        unique_tracks['audio_features'] = unique_tracks['Song_ID'].apply(lambda x: get_audio_features(x, sp))
        unique_tracks['emotion'] = unique_tracks['audio_features'].apply(predict_emotion)

    # Unir las emociones de regreso al DataFrame principal
    df = df.merge(unique_tracks[['Song_ID', 'emotion']], on='Song_ID', how='left')

    # Calcular y mostrar el Artista Principal
    artista_favorito = df["Artist_name"].value_counts().idxmax()
    st.write(f"**Artista más escuchado:** {artista_favorito}")

    # Calcular la canción favorita del artista principal
    fav_song_df = df[(df['Artist_name'] == artista_favorito)]
    if not fav_song_df.empty:
        cancion_favorita = fav_song_df['Song_Name'].value_counts().idxmax()
        st.write(f"**Canción favorita de {artista_favorito}:** {cancion_favorita}")

        # Obtener la emoción de esa canción en específico
        fav_track_id = fav_song_df[fav_song_df['Song_Name'] == cancion_favorita]['Song_ID'].iloc[0]
        fav_song_emotion = df[(df['Song_ID'] == fav_track_id)]['emotion'].iloc[0]
        
        if fav_song_emotion != "Desconocida":
            st.subheader(f"Emoción de '{cancion_favorita}':")
            st.success(f"La emoción asociada a {cancion_favorita} es: {fav_song_emotion}")
        else:
            st.warning("No se pudo predecir la emoción para tu canción favorita.")

    st.separator()
    st.subheader("Análisis de Emociones en tus Escuchas Recientes:")

    # --- Gráfica 1: Distribución General ---
    st.markdown("##### Distribución General de Emociones")
    emotion_counts = df['emotion'].value_counts().reset_index()
    emotion_counts.columns = ['Emoción', 'Cantidad']
    fig_emotion_dist = px.pie(emotion_counts, values='Cantidad', names='Emoción', title='Distribución General de Emociones en tus Escuchas')
    st.plotly_chart(fig_emotion_dist, use_container_width=True)

    # --- Gráfica 2: Emociones por Hora ---
    st.markdown("##### Emociones por Hora del Día")
    emotion_by_hour = df.groupby(['hour_of_day', 'emotion']).size().unstack(fill_value=0)
    if not emotion_by_hour.empty:
        fig_hour_emotion = px.bar(emotion_by_hour,
                                   x=emotion_by_hour.index,
                                   y=emotion_by_hour.columns,
                                   title='Distribución de Emociones por Hora del Día',
                                   labels={'hour_of_day': 'Hora del Día', 'value': 'Cantidad de Canciones', 'variable': 'Emoción'},
                                   barmode='group')
        st.plotly_chart(fig_hour_emotion, use_container_width=True)
    else:
        st.info("No hay suficientes datos para mostrar la distribución de emociones por hora.")

    # --- Gráfica 3: Emociones por Día ---
    st.markdown("##### Emociones por Día de la Semana")
    emotion_by_day = df.groupby(['day_of_week', 'emotion']).size().unstack(fill_value=0)
    if not emotion_by_day.empty:
        fig_day_emotion = px.bar(emotion_by_day,
                                  x=emotion_by_day.index,
                                  y=emotion_by_day.columns,
                                  title='Distribución de Emociones por Día de la Semana',
                                  labels={'day_of_week': 'Día de la Semana', 'value': 'Cantidad de Canciones', 'variable': 'Emoción'},
                                  barmode='group')
        st.plotly_chart(fig_day_emotion, use_container_width=True)
    else:
        st.info("No hay suficientes datos para mostrar la distribución de emociones por día.")

    # --- Historial Completo ---
    st.subheader("Todas las canciones recientes con sus emociones:")
    st.dataframe(df[['Song_Name', 'Artist_name', 'emotion', 'played_at']], use_container_width=True)

else:
    if sp is None:
        st.error("No se pudo establecer conexión con Spotify. Por favor, revisa tus credenciales CLIENT_ID y CLIENT_SECRET.")
    else:
        st.error(f"❌ El archivo `{csv_filename}` no se encuentra en el repositorio. Recuerda subir el archivo CSV generado en tu Colab.")
