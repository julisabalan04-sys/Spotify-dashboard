import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

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
        st.error(f"Error al obtener las características de audio: {e}")
        return None

# Función para predecir la emoción basada en las características de audio (heurística simple)
def predict_emotion(features):
    if not features:
        return "No se pudieron obtener características para predecir la emoción."

    valence = features.get('valence', 0.5)  # Positividad musical (0.0 a 1.0)
    energy = features.get('energy', 0.5)    # Intensidad y actividad (0.0 a 1.0)
    danceability = features.get('danceability', 0.5) # Qué tan bailable es la pista (0.0 a 1.0)

    if valence > 0.7 and energy > 0.7:
        return "¡Feliz y Energético! 😄"
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
st.markdown("Esta aplicación predice el tipo de emoción de tu canción favorita de tu artista más escuchado, basándose en sus características de audio de Spotify.")

st.header("Tus Preferencias Musicales:")

# Recuperar datos del estado del kernel
# Estas variables deberían estar definidas si las celdas anteriores se ejecutaron exitosamente
if 'artista_favorito' in globals() and 'cancion_favorita' in globals() and 'df' in globals() and 'sp' in globals():
    st.write(f"**Artista más escuchado:** {artista_favorito}")
    st.write(f"**Canción favorita de {artista_favorito}:** {cancion_favorita}")

    # Obtener el ID de la canción favorita
    fav_song_df = df[(df['Artist_name'] == artista_favorito) & (df['Song_Name'] == cancion_favorita)]
    track_id = None
    if not fav_song_df.empty:
        track_id = fav_song_df['Song_ID'].iloc[0] # Tomar el primer ID si hay duplicados
        st.write(f"**ID de la canción:** `{track_id}`")
    else:
        st.error(f"⚠️ No se encontró el ID de la canción '{cancion_favorita}' del artista '{artista_favorito}'. Asegúrate de que la canción exista en tus datos recientes.")

    if track_id:
        st.subheader("Características de Audio de la Canción Favorita:")
        features = get_audio_features(track_id, sp)

        if features:
            features_df = pd.DataFrame([features]).T.rename(columns={0: 'Valor'}) # Transponer para mejor visualización
            st.dataframe(features_df.style.format("{:.2f}")) # Formatear números para legibilidad

            st.subheader("Emoción Predicha:")
            emotion = predict_emotion(features)
            st.success(f"La emoción asociada a '\"{cancion_favorita}\"' es: **{emotion}**")
        else:
            st.warning("No se pudieron obtener las características de audio para esta canción.")
    else:
        st.info("No se puede predecir la emoción sin el ID de la canción. Por favor, asegúrate de que la canción esté en tus reproducciones recientes.")
else:
    st.error("Las variables necesarias ('artista_favorito', 'cancion_favorita', 'df', 'sp') no se encontraron en el entorno. Por favor, ejecuta las celdas anteriores para cargar los datos.")

st.markdown("---")
st.markdown("**Instrucciones para ejecutar la aplicación:**")
st.markdown("1. **Instala Streamlit** (si aún no lo has hecho): `!pip install streamlit`")
st.markdown("2. **Guarda este código** en un archivo llamado `app.py` (o cualquier otro nombre con extensión `.py`).")
st.markdown("3. **Ejecuta la aplicación** desde tu terminal con: `streamlit run app.py`")
