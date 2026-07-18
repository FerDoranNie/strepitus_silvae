"""Strepitus Silvae — field observations to Darwin Core records."""

import json
import os
from datetime import date
from typing import Any

import streamlit as st

from export import observations_to_csv
from services import analyze_audio, analyze_image

MODEL_OPTIONS = {
    "GPT-5.6 Sol — máxima capacidad": "gpt-5.6-sol",
    "GPT-5.6 Terra — equilibrio entre calidad y costo": "gpt-5.6-terra",
    "GPT-5.6 Luna — alto volumen y costo reducido": "gpt-5.6-luna",
}

DARWIN_CORE_COLUMNS = [
    "scientificName", "vernacularName", "individualCount", "behavior", "organismRemarks",
    "eventDate", "decimalLatitude", "decimalLongitude", "locality", "basisOfRecord", "identifiedBy",
]


def render_analysis_result(result: dict[str, Any]) -> None:
    """Render a review-first dashboard for a validated observation."""
    confidence = result["identificationConfidence"]
    confidence_label = {"alto": "Alta", "medio": "Media", "bajo": "Baja"}[confidence]
    confidence_color = {"alto": "#1b7f3a", "medio": "#a86b00", "bajo": "#a12222"}[confidence]
    validation = result.get("validacionExterna")

    st.subheader("Resultado para revisión")
    col_species, col_count, col_confidence = st.columns(3)
    col_species.metric("Especie propuesta", result["vernacularName"] or "Sin determinar")
    col_count.metric("Individuos", result["individualCount"])
    col_confidence.markdown(
        f"<div style='margin-top: 0.4rem; color: {confidence_color}; font-weight: 700;'>"
        f"Confianza {confidence_label}</div>", unsafe_allow_html=True,
    )

    if result["alertaHumanaOVehiculo"]:
        st.warning("⚠️ Posible presencia humana o vehículo: verifica el evento de inmediato.")
    else:
        st.success("Sin alerta humana o de vehículo detectada en esta evidencia.")

    st.subheader("Trazabilidad de agentes")
    trace = [
        {"Agente": "Vision-Ecologist" if not result.get("transcripcion") else "Audio-Structurer", "Estado": "Completado", "Resultado": f"Confianza {confidence_label.lower()}"},
        {"Agente": "Taxonomic Validator", "Estado": "Activado" if validation else "No requerido", "Resultado": "Consulta iNaturalist" if validation else "Solo se activa con confianza media o baja"},
        {"Agente": "Schema Validator", "Estado": "Completado", "Resultado": "Registro Darwin Core-aligned válido"},
    ]
    st.dataframe(trace, hide_index=True, use_container_width=True)

    if validation:
        st.subheader("Validación taxonómica externa")
        if validation.get("validacionExitosa"):
            st.info(
                f"iNaturalist encontró **{validation.get('nombreCientificoOficial', 'una coincidencia')}** "
                f"(ID: {validation.get('idTaxonomico', 'no disponible')})."
            )
        else:
            st.warning(validation.get("mensaje", "La consulta a iNaturalist no devolvió una coincidencia."))

    if result.get("transcripcion"):
        with st.expander("Transcripción original"):
            st.write(result["transcripcion"])

    st.subheader("Registro Darwin Core extendido")
    st.dataframe([{key: result.get(key) for key in DARWIN_CORE_COLUMNS}], hide_index=True, use_container_width=True)
    with st.expander("JSON completo"):
        st.json(result)

st.set_page_config(page_title="Strepitus Silvae", page_icon="🌿", layout="wide")

st.title("🌿 Strepitus Silvae")
st.caption("Copiloto de campo para transformar evidencia de fauna en registros Darwin Core verificables.")

with st.sidebar:
    st.header("Configuración")
    env_model = os.getenv("OPENAI_MODEL", "gpt-5.6-sol")
    default_label = next((label for label, model_id in MODEL_OPTIONS.items() if model_id == env_model), None)
    selected_label = st.selectbox(
        "Modelo de análisis", list(MODEL_OPTIONS),
        index=list(MODEL_OPTIONS).index(default_label) if default_label else 0,
    )
    model = MODEL_OPTIONS[selected_label]
    if st.checkbox("Usar un identificador de modelo personalizado"):
        model = st.text_input("Identificador personalizado", value=env_model)
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
            render_analysis_result(result)
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
