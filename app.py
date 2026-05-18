import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import plotly.express as px
import pytz # Import pytz for timezone conversion

# Asume que 'sp', 'df', 'artista_favorito', 'cancion_favorita' están disponibles
# del entorno de Colab después de ejecutar las celdas anteriores.

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
        else:
            return None
    except Exception as e:
        # st.error(f"Error al obtener las características de audio para {track_id}: {e}") # Comment out for cleaner app
        return None

# Función para predecir la emoción basada en las características de audio (heurística simple)
def predict_emotion(features):
    if not features:
        return "Desconocida" # Changed from a long string for plotting

    valence = features.get('valence', 0.5)  # Positividad musical (0.0 a 1.0)
    energy = features.get('energy', 0.5)    # Intensidad y actividad (0.0 a 1.0)
    danceability = features.get('danceability', 0.5) # Qué tan bailable es la pista (0.0 a 1.0)

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

# Recuperar datos del estado del kernel
if 'df' in globals() and 'sp' in globals():
    # Ensure 'played_at' is datetime and timezone-converted if not already
    # This might be redundant if df is already processed in Colab, but good for robustness
    if not pd.api.types.is_datetime64_any_dtype(df['played_at']):
        df['played_at'] = pd.to_datetime(df['played_at'])
        mexico_tz = pytz.timezone('America/Mexico_City')
        df['played_at'] = df['played_at'].dt.tz_convert(mexico_tz)

    # Calculate hour and day for further analysis
    df['hour_of_day'] = df['played_at'].dt.hour
    df['day_of_week'] = df['played_at'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=day_order, ordered=True)

    # Get unique tracks to avoid redundant API calls
    unique_tracks = df[['Song_ID', 'Song_Name', 'Artist_name']].drop_duplicates(subset=['Song_ID']).copy()
    unique_tracks['audio_features'] = unique_tracks['Song_ID'].apply(lambda x: get_audio_features(x, sp))
    unique_tracks['emotion'] = unique_tracks['audio_features'].apply(predict_emotion)

    # Merge emotions back to the main DataFrame
    df = df.merge(unique_tracks[['Song_ID', 'emotion']], on='Song_ID', how='left')


    # Display Top Artist and Favorite Song if available
    artista_favorito = df["Artist_name"].value_counts().idxmax()
    st.write(f"**Artista más escuchado:** {artista_favorito}")

    # Determine the most frequent song for the favorite artist
    fav_song_df = df[(df['Artist_name'] == artista_favorito)]
    if not fav_song_df.empty:
        cancion_favorita = fav_song_df['Song_Name'].value_counts().idxmax()
        st.write(f"**Canción favorita de {artista_favorito}:** {cancion_favorita}")

        # Display emotion for the specific favorite song (using the existing logic)
        fav_track_id = fav_song_df[fav_song_df['Song_Name'] == cancion_favorita]['Song_ID'].iloc[0]
        fav_song_emotion = df[(df['Song_ID'] == fav_track_id)]['emotion'].iloc[0]
        if fav_song_emotion != "Desconocida":
            st.subheader(f"Emoción de '{cancion_favorita}':")
            st.success(f"La emoción asociada a '{cancion_favorita}' es: **{fav_song_emotion}**")
        else:
            st.warning("No se pudo predecir la emoción para tu canción favorita.")

    st.subheader("Análisis de Emociones en tus Escuchas Recientes:")

    # Overall Emotion Distribution
    st.markdown("##### Distribución General de Emociones")
    emotion_counts = df['emotion'].value_counts().reset_index()
    emotion_counts.columns = ['Emoción', 'Cantidad']
    fig_emotion_dist = px.pie(emotion_counts, values='Cantidad', names='Emoción', title='Distribución General de Emociones en tus Escuchas')
    st.plotly_chart(fig_emotion_dist, use_container_width=True)

    # Emotion by Hour of Day
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

    # Emotion by Day of Week
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


    st.subheader("Todas las canciones recientes con sus emociones:")
    st.dataframe(df[['Song_Name', 'Artist_name', 'emotion', 'played_at']], use_container_width=True)


else:
    st.error("Las variables necesarias ('df', 'sp') no se encontraron en el entorno. Por favor, ejecuta las celdas anteriores para cargar los datos.")
    if 'artista_favorito' not in globals():
        st.warning("`artista_favorito` no está definido. Asegúrate de ejecutar la celda que lo calcula.")
    if 'cancion_favorita' not in globals():
        st.warning("`cancion_favorita` no está definido. Asegúrate de ejecutar la celda que lo calcula.")


st.markdown("---")
st.markdown("**Instrucciones para ejecutar la aplicación:**")
st.markdown("1. **Instala Streamlit** (si aún no lo has hecho): `!pip install streamlit`")
st.markdown("2. **Guarda este código** en un archivo llamado `app.py` (o cualquier otro nombre con extensión `.py`).")
st.markdown("3. **Ejecuta la aplicación** desde tu terminal con: `streamlit run app.py`")
