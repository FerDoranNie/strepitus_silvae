"""Strepitus Silvae — field observations to Darwin Core records."""

import json
import os
from datetime import date

import streamlit as st

from export import observations_to_csv
from services import analyze_audio, analyze_image

st.set_page_config(page_title="Strepitus Silvae", page_icon="🌿", layout="wide")

st.title("🌿 Strepitus Silvae")
st.caption("Copiloto de campo para transformar evidencia de fauna en registros Darwin Core verificables.")

with st.sidebar:
    st.header("Configuración")
    model = st.text_input("Modelo de análisis", value=os.getenv("OPENAI_MODEL", "gpt-5.6"))
    st.caption("La clave se lee exclusivamente desde `OPENAI_API_KEY` en el entorno.")

tab_image, tab_audio = st.tabs(["📷 Cámara trampa", "🎙️ Nota de voz"])

with tab_image:
    upload = st.file_uploader("Carga una foto de cámara trampa", type=["jpg", "jpeg", "png", "webp"])
    if upload:
        st.image(upload, caption=upload.name, use_container_width=True)

with tab_audio:
    audio = st.audio_input("Graba una nota de campo")
    audio_upload = st.file_uploader("o carga un audio", type=["mp3", "wav", "m4a", "ogg"], key="audio_file")

st.divider()
st.subheader("Contexto del evento")
col1, col2, col3 = st.columns(3)
with col1:
    event_date = st.date_input("Fecha", value=date.today())
with col2:
    latitude = st.text_input("Latitud (opcional)", placeholder="19.4326")
with col3:
    longitude = st.text_input("Longitud (opcional)", placeholder="-99.1332")
locality = st.text_input("Localidad (opcional)", placeholder="Reserva / estación de monitoreo")

if st.button("Analizar evidencia", type="primary", use_container_width=True):
    evidence = upload or audio or audio_upload
    if not evidence:
        st.error("Carga una imagen o graba/carga un audio antes de analizar.")
    elif not os.getenv("OPENAI_API_KEY"):
        st.error("Falta `OPENAI_API_KEY`. Agrégala a tus variables de entorno y reinicia la app.")
    else:
        context = {
            "eventDate": event_date.isoformat(),
            "decimalLatitude": latitude or None,
            "decimalLongitude": longitude or None,
            "locality": locality or None,
        }
        try:
            with st.spinner("El equipo de agentes está procesando la evidencia…"):
                if upload:
                    result = analyze_image(upload.getvalue(), upload.type or "image/jpeg", model, context)
                else:
                    source = audio or audio_upload
                    result = analyze_audio(source.getvalue(), source.name, source.type or "audio/wav", model, context)
            st.success("Registro listo para revisión humana.")
            if result.get("transcripcion"):
                with st.expander("Transcripción original"):
                    st.write(result["transcripcion"])
            if result.get("alertaHumanaOVehiculo"):
                st.warning("⚠️ Posible presencia humana o vehículo: verifica el evento de inmediato.")
            st.subheader("Registro Darwin Core extendido")
            st.json(result)
            st.download_button(
                "Descargar JSON", json.dumps(result, ensure_ascii=False, indent=2),
                file_name="strepitus_observation.json", mime="application/json", use_container_width=True,
            )
            st.download_button(
                "Descargar CSV Darwin Core", observations_to_csv([result]).encode("utf-8-sig"),
                file_name="strepitus_observation.csv", mime="text/csv", use_container_width=True,
            )
        except Exception as error:
            st.error(f"No fue posible procesar la evidencia: {error}")

st.caption("La identificación es una hipótesis asistida por IA y requiere revisión de personal capacitado.")
