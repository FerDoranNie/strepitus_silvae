"""Strepitus Silvae — field observations to Darwin Core records."""

import json
import os
from datetime import date
from typing import Any

import folium
import streamlit as st
from pyinaturalist import get_taxa
from streamlit_folium import st_folium

from ecological_context import (
    ICONIC_TAXA,
    gbif_potential_species,
    gbif_species_url,
    potential_species,
    taxon_search_url,
    wikipedia_search_url,
)
from export import observations_to_csv
from habitat_context import habitat_profile
from services import analyze_audio, analyze_bird_audio, analyze_image, analyze_video

MODEL_OPTIONS = {
    "GPT-5.6 Sol — máxima capacidad": "gpt-5.6-sol",
    "GPT-5.6 Terra — equilibrio entre calidad y costo": "gpt-5.6-terra",
    "GPT-5.6 Luna — alto volumen y costo reducido": "gpt-5.6-luna",
}

DARWIN_CORE_COLUMNS = [
    "scientificName", "vernacularName", "individualCount", "behavior", "organismRemarks",
    "eventDate", "decimalLatitude", "decimalLongitude", "locality", "basisOfRecord", "identifiedBy",
]


@st.cache_data(ttl=3600, show_spinner=False)
def cached_potential_species(latitude: float, longitude: float, radius_km: int, group: str) -> list[dict[str, Any]]:
    """Cache read-only community observations, never evidence-analysis results."""
    return potential_species(latitude, longitude, radius_km, group)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_gbif_potential_species(latitude: float, longitude: float, radius_km: int, group: str) -> list[dict[str, Any]]:
    """Cache GBIF's read-only occurrence context independently from iNaturalist."""
    return gbif_potential_species(latitude, longitude, radius_km, group)


@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def cached_habitat_profile(latitude: float, longitude: float, radius_km: int) -> dict[str, Any]:
    """Cache lightweight terrain and OSM context for repeated map interactions."""
    return habitat_profile(latitude, longitude, radius_km)


def load_potential_species(latitude: float, longitude: float, radius_km: int, group: str, source: str) -> list[dict[str, Any]]:
    """Load selected ecological context without changing evidence-based confidence."""
    results = []
    if source in {"Ambas", "iNaturalist"}:
        results.extend(cached_potential_species(latitude, longitude, radius_km, group))
    if source in {"Ambas", "GBIF"}:
        results.extend(cached_gbif_potential_species(latitude, longitude, radius_km, group))
    return results


def save_potential_species(latitude: float, longitude: float, radius_km: int, group: str, source: str) -> None:
    """Persist the context table across Streamlit reruns in this browser session."""
    st.session_state["potential_species_results"] = load_potential_species(latitude, longitude, radius_km, group, source)
    st.session_state["potential_species_description"] = f"{source} · {group} · radio aproximado de {radius_km} km"


def save_habitat_profile(latitude: float, longitude: float, radius_km: int) -> None:
    """Persist a profile independently from the species and evidence results."""
    st.session_state["habitat_profile"] = cached_habitat_profile(latitude, longitude, radius_km)


@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def cached_taxon_matches(query: str) -> list[dict[str, Any]]:
    """Look up a human-proposed taxon in iNaturalist without changing the AI record."""
    response = get_taxa(q=query, rank="species", per_page=5)
    matches = response.get("results", [])
    rows = []
    for match in matches:
        scientific_name = match.get("name") or query
        taxon_id = match.get("id")
        rows.append(
            {
                "Propuesta humana": query,
                "Coincidencia iNaturalist": scientific_name,
                "Nombre común": match.get("preferred_common_name") or "—",
                "Rango": match.get("rank") or "—",
                "Ficha iNaturalist": f"https://www.inaturalist.org/taxa/{taxon_id}" if taxon_id else taxon_search_url(scientific_name),
                "GBIF": gbif_species_url(None, scientific_name),
                "Wikipedia": wikipedia_search_url(scientific_name),
            }
        )
    return rows


def proposed_species_from_text(value: str) -> list[str]:
    """Keep a short, de-duplicated list of candidate taxa entered by a reviewer."""
    proposed = []
    for line in value.splitlines():
        candidate = line.strip(" -•\t")
        if candidate and candidate.casefold() not in {item.casefold() for item in proposed}:
            proposed.append(candidate)
    return proposed[:8]


def ensure_species_links(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Backfill external links for results kept from an earlier session-state shape."""
    enriched = []
    for result in results:
        row = dict(result)
        scientific_name = row.get("Nombre científico", "")
        if row.get("Fuente") == "iNaturalist":
            row.setdefault("Ficha taxonómica", taxon_search_url(scientific_name))
        elif row.get("Fuente") == "GBIF":
            row.setdefault("Ficha taxonómica", gbif_species_url(None, scientific_name))
        row.setdefault("Wikipedia", wikipedia_search_url(scientific_name))
        enriched.append(row)
    return enriched


def selected_coordinates() -> tuple[float | None, float | None]:
    """Read optional coordinate widgets without accepting invalid values."""
    try:
        latitude = float(st.session_state.get("latitude_input", ""))
        longitude = float(st.session_state.get("longitude_input", ""))
    except (TypeError, ValueError):
        return None, None
    if -90 <= latitude <= 90 and -180 <= longitude <= 180:
        return latitude, longitude
    return None, None


def matching_habitat_profile(latitude: float | None, longitude: float | None) -> dict[str, Any] | None:
    """Only draw infrastructure when it belongs to the currently selected point."""
    profile = st.session_state.get("habitat_profile")
    if not profile or latitude is None or longitude is None:
        return None
    if abs(profile["latitude"] - latitude) > 0.000001 or abs(profile["longitude"] - longitude) > 0.000001:
        return None
    return profile


def render_location_context() -> tuple[date, float | None, float | None, str]:
    """Render point selection and independent ecological-context lookup."""
    st.subheader("Contexto del evento")
    st.caption("Haz clic en el mapa o captura las coordenadas manualmente. El mapa no modifica la identificación de la evidencia.")

    current_latitude, current_longitude = selected_coordinates()
    map_center = [current_latitude, current_longitude] if current_latitude is not None else [19.4326, -99.1332]
    field_map = folium.Map(location=map_center, zoom_start=12 if current_latitude is not None else 5, control_scale=True)
    folium.ClickForMarker(popup="Punto del evento").add_to(field_map)
    if current_latitude is not None and current_longitude is not None:
        folium.Marker([current_latitude, current_longitude], tooltip="Punto del evento").add_to(field_map)
        profile = matching_habitat_profile(current_latitude, current_longitude)
        radius_m = profile["radius_m"] if profile else min(st.session_state.get("potential_radius", 5) * 1000, 1_000)
        folium.Circle([current_latitude, current_longitude], radius=radius_m, color="#2d6a4f", fill=False, tooltip="Área de perfil ambiental").add_to(field_map)
        if profile:
            vegetation_name = profile.get("potential_vegetation", "Vegetación potencial no disponible")
            koppen_class = profile.get("koppen_class") or "—"
            folium.Circle(
                [current_latitude, current_longitude],
                radius=radius_m,
                color=profile.get("vegetation_color", "#6b7280"),
                weight=2,
                fill=True,
                fill_opacity=0.18,
                tooltip=f"Vegetación potencial: {vegetation_name}",
                popup=f"Köppen aproximado: {koppen_class}<br>Vegetación potencial: {vegetation_name}",
            ).add_to(field_map)
            folium.raster_layers.WmsTileLayer(
                url="https://services.terrascope.be/wms/v2",
                layers="WORLDCOVER_2021_MAP",
                fmt="image/png",
                transparent=True,
                attr="© ESA WorldCover 2021 / Copernicus Sentinel data",
                name="Cobertura de suelo ESA WorldCover (2021)",
                overlay=True,
                control=True,
                show=False,
                opacity=0.65,
            ).add_to(field_map)
            if profile["building_features"]:
                folium.GeoJson(
                    {"type": "FeatureCollection", "features": profile["building_features"]},
                    name="Edificios OSM",
                    style_function=lambda _: {"color": "#b5651d", "weight": 1, "fillColor": "#dca55b", "fillOpacity": 0.45},
                ).add_to(field_map)
            if profile["road_features"]:
                folium.GeoJson(
                    {"type": "FeatureCollection", "features": profile["road_features"]},
                    name="Vías OSM",
                    style_function=lambda _: {"color": "#6c757d", "weight": 2},
                ).add_to(field_map)
            folium.LayerControl().add_to(field_map)

    map_data = st_folium(field_map, key="event_location_map", height=320, width=700, returned_objects=["last_clicked"])
    clicked_point = map_data.get("last_clicked") if map_data else None
    if clicked_point:
        clicked_latitude = clicked_point.get("lat")
        clicked_longitude = clicked_point.get("lng")
        if clicked_latitude is not None and clicked_longitude is not None:
            next_latitude, next_longitude = float(clicked_latitude), float(clicked_longitude)
            if current_latitude is None or abs(current_latitude - next_latitude) > 0.000001 or abs(current_longitude - next_longitude) > 0.000001:
                st.session_state["latitude_input"] = f"{next_latitude:.6f}"
                st.session_state["longitude_input"] = f"{next_longitude:.6f}"
                st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        event_date = st.date_input("Fecha", value=date.today())
    with col2:
        st.text_input("Latitud (opcional)", placeholder="19.4326", key="latitude_input")
    with col3:
        st.text_input("Longitud (opcional)", placeholder="-99.1332", key="longitude_input")
    locality = st.text_input("Localidad (opcional)", placeholder="Reserva / estación de monitoreo")

    latitude, longitude = selected_coordinates()
    return event_date, latitude, longitude, locality


def render_potential_species_section(latitude: float | None, longitude: float | None, allow_actions: bool) -> None:
    """Render nearby-species results; filters belong only in the dedicated tab."""
    st.subheader("Especies potenciales cercanas")
    st.caption("Contexto de iNaturalist y/o GBIF de los últimos cinco años; no es presencia confirmada ni sustituye la evidencia.")

    if allow_actions:
        source_col, filter_col, radius_col, action_col = st.columns(4, vertical_alignment="bottom")
        with source_col:
            source = st.selectbox("Fuente", ["Ambas", "iNaturalist", "GBIF"], key="potential_source")
        with filter_col:
            group = st.selectbox("Grupo", list(ICONIC_TAXA), key="potential_group")
        with radius_col:
            radius_km = st.selectbox(
                "Radio", [1, 5, 10, 25, 50], index=2,
                format_func=lambda value: f"{value} km", key="potential_radius",
            )
        with action_col:
            lookup = st.button("Consultar fuentes", key="potential_species_button", width="stretch")

        if lookup:
            if latitude is None or longitude is None:
                st.warning("Selecciona un punto en el mapa o escribe latitud y longitud válidas.")
            else:
                try:
                    with st.spinner("Consultando observaciones comunitarias…"):
                        save_potential_species(latitude, longitude, radius_km, group, source)
                    st.rerun()
                except Exception as error:
                    st.error(f"No fue posible consultar las fuentes: {error}")

    results = st.session_state.get("potential_species_results")
    if results is None:
        if not allow_actions:
            st.info("Aún no hay una consulta de especies cercanas para mostrar.")
        return

    results = ensure_species_links(results)
    st.session_state["potential_species_results"] = results
    st.caption(st.session_state.get("potential_species_description", "Resultados de iNaturalist"))
    st.caption("Más registros indican mayor relevancia para revisión; no confirman presencia actual ni cambian la confianza de la identificación.")
    if not results:
        st.info("No hubo especies con el filtro seleccionado.")
        return

    st.dataframe(
        results,
        hide_index=True,
        width="stretch",
        column_config={
            "Ficha taxonómica": st.column_config.LinkColumn("Ficha de la fuente", display_text="Abrir ficha"),
            "Wikipedia": st.column_config.LinkColumn("Wikipedia", display_text="Buscar"),
        },
    )
    with st.expander("Enlaces de especies potenciales"):
        for row in results:
            scientific_name = row.get("Nombre científico", "Especie sin nombre")
            source = row.get("Fuente", "fuente")
            st.markdown(
                f"**{scientific_name}** · [{source}]({row['Ficha taxonómica']}) · "
                f"[Wikipedia]({row['Wikipedia']})"
            )


def render_habitat_profile_section(latitude: float | None, longitude: float | None, allow_actions: bool) -> None:
    """Render environmental results; the refresh action belongs in its dedicated tab."""
    st.subheader("Perfil ambiental del punto")
    st.caption("Elevación de Copernicus DEM vía Open-Meteo; infraestructura mapeada en OpenStreetMap. El radio de infraestructura se limita a 1 km para respetar el servicio público.")

    if allow_actions:
        refresh_habitat = st.button("Actualizar perfil ambiental", key="habitat_profile_button", width="stretch")
        if refresh_habitat:
            if latitude is None or longitude is None:
                st.warning("Selecciona un punto en el mapa o escribe latitud y longitud válidas.")
            else:
                try:
                    radius_km = st.session_state.get("potential_radius", 10)
                    with st.spinner("Consultando terreno e infraestructura mapeada…"):
                        save_habitat_profile(latitude, longitude, radius_km)
                    st.rerun()
                except Exception as error:
                    st.error(f"No fue posible consultar el perfil ambiental: {error}")

    profile = matching_habitat_profile(latitude, longitude)
    if not profile:
        if not allow_actions:
            st.info("Aún no hay un perfil ambiental para mostrar.")
        return

    metrics = st.columns(4)
    metrics[0].metric("Elevación", f"{profile['elevation_m']} m" if profile["elevation_m"] is not None else "No disponible")
    metrics[1].metric("Relieve local", f"{profile['local_relief_m']} m" if profile["local_relief_m"] is not None else "No disponible")
    metrics[2].metric("Edificios mapeados", profile["mapped_buildings"])
    metrics[3].metric("Vías visualizadas", f"{profile['mapped_road_length_km']} km")
    st.markdown(
        f"**Clima Köppen aproximado:** `{profile.get('koppen_class') or '—'}` "
        f"— {profile.get('koppen_label', 'No disponible')}"
    )
    st.markdown(f"**Vegetación potencial inferida:** {profile.get('potential_vegetation', 'No disponible')}")
    st.caption(
        f"Normales climáticas: {profile.get('climate_period', '—')}. Activa la capa “Cobertura de suelo ESA WorldCover (2021)” en el control del mapa para ver cobertura observada; no equivale a vegetación potencial."
    )
    st.caption(f"Radio analizado: {profile['radius_m'] / 1000:g} km · Las capas naranja y gris son una muestra limitada de OpenStreetMap; pueden estar incompletas.")


def render_human_review(show_controls: bool, review_key: str = "human_review") -> None:
    """Preserve expert corrections separately from the original AI output."""
    review = st.session_state.get(review_key)
    if review:
        verdict_labels = {
            "Correcta": "Confirmada por revisión humana",
            "Parcial": "Aciertos y errores: revisión humana parcial",
            "Incorrecta": "Identificación rechazada por revisión humana",
        }
        st.info(verdict_labels[review["verdict"]])
        if review["proposed_species"]:
            st.markdown("**Especies propuestas por la persona revisora:** " + ", ".join(review["proposed_species"]))
        if review["notes"]:
            st.caption(f"Notas de revisión: {review['notes']}")

        matches = review.get("taxon_matches", [])
        if matches:
            st.caption("Coincidencias reconsultadas en iNaturalist; GBIF y Wikipedia se incluyen para la verificación final.")
            st.dataframe(
                matches,
                hide_index=True,
                width="stretch",
                column_config={
                    "Ficha iNaturalist": st.column_config.LinkColumn("iNaturalist", display_text="Abrir ficha"),
                    "GBIF": st.column_config.LinkColumn("GBIF", display_text="Buscar"),
                    "Wikipedia": st.column_config.LinkColumn("Wikipedia", display_text="Buscar"),
                },
            )
        elif review["proposed_species"]:
            st.warning("No se encontró una coincidencia de especie exacta en iNaturalist. Revisa la ortografía o usa un nombre científico.")

    if not show_controls:
        return

    st.subheader("Corrección humana")
    st.caption("La corrección queda separada de la hipótesis original de IA para conservar la trazabilidad del registro.")
    verdict_widget_key = f"{review_key}_verdict"
    proposed_widget_key = f"{review_key}_proposed_species"
    notes_widget_key = f"{review_key}_notes"
    if review:
        st.session_state.setdefault(verdict_widget_key, review["verdict"])
        st.session_state.setdefault(proposed_widget_key, "\n".join(review["proposed_species"]))
        st.session_state.setdefault(notes_widget_key, review["notes"])

    with st.form(f"{review_key}_form", border=True):
        default_verdict = review["verdict"] if review else "Correcta"
        verdict = st.segmented_control(
            "Veredicto de la identificación",
            ["Correcta", "Parcial", "Incorrecta"],
            default=default_verdict,
            key=verdict_widget_key,
        )
        proposed_text = st.text_area(
            "Especie(s) propuesta(s)",
            placeholder="Una por línea, idealmente en nombre científico.\nEj.: Panthera onca\nTapirus bairdii",
            help="Para una corrección parcial, escribe todas las especies que sí deben permanecer y las que deben añadirse o sustituirse.",
            key=proposed_widget_key,
        )
        notes = st.text_area(
            "Notas de la persona revisora (opcional)",
            placeholder="Por qué es correcta, parcial o incorrecta.",
            key=notes_widget_key,
        )
        submitted = st.form_submit_button("Guardar corrección y reconsultar especies", width="stretch")

    if not submitted:
        return

    proposed_species = proposed_species_from_text(proposed_text)
    if verdict in {"Parcial", "Incorrecta"} and not proposed_species:
        st.error("Para una revisión parcial o incorrecta, propone al menos una especie para volver a consultar.")
        return

    try:
        with st.spinner("Verificando las especies propuestas en iNaturalist…"):
            taxon_matches = [match for name in proposed_species for match in cached_taxon_matches(name)]
        st.session_state[review_key] = {
            "verdict": verdict,
            "proposed_species": proposed_species,
            "notes": notes.strip(),
            "taxon_matches": taxon_matches,
        }
        st.rerun()
    except Exception as error:
        st.error(f"No fue posible verificar las especies propuestas: {error}")


def render_analysis_result(
    result: dict[str, Any], show_review_controls: bool = False, review_key: str = "human_review"
) -> None:
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
    st.dataframe(trace, hide_index=True, width="stretch")

    if validation:
        st.subheader("Validación taxonómica externa")
        if validation.get("validacionExitosa"):
            st.info(
                f"iNaturalist encontró **{validation.get('nombreCientificoOficial', 'una coincidencia')}** "
                f"(ID: {validation.get('idTaxonomico', 'no disponible')})."
            )
        else:
            st.warning(validation.get("mensaje", "La consulta a iNaturalist no devolvió una coincidencia."))

    render_human_review(show_review_controls, review_key)

    if result.get("bioacousticCandidates"):
        st.subheader("Candidatos bioacústicos de BirdNET (beta)")
        st.dataframe(result["bioacousticCandidates"], hide_index=True, width="stretch")

    if result.get("transcripcion"):
        with st.expander("Transcripción original"):
            st.write(result["transcripcion"])

    st.subheader("Registro Darwin Core extendido")
    st.dataframe([{key: result.get(key) for key in DARWIN_CORE_COLUMNS}], hide_index=True, width="stretch")
    with st.expander("JSON completo"):
        st.json(result)


def render_analysis_results(results: list[dict[str, Any]], show_review_controls: bool = False) -> None:
    """Render one result or a reviewable set of distinct video detections."""
    if len(results) == 1:
        render_analysis_result(results[0], show_review_controls=show_review_controls)
        return

    st.subheader("Detecciones multiespecie del video")
    st.caption("Cada fila corresponde a un taxón distinto; apariciones repetidas se consolidan antes de exportar.")
    st.dataframe(
        [
            {
                "Especie propuesta": result["vernacularName"] or result["scientificName"] or "Sin determinar",
                "Nombre científico": result["scientificName"] or "—",
                "Máx. individuos visibles": result["individualCount"],
                "Confianza": result["identificationConfidence"],
            }
            for result in results
        ],
        hide_index=True,
        width="stretch",
    )
    for index, result in enumerate(results, start=1):
        species_name = result["vernacularName"] or result["scientificName"] or f"Detección {index}"
        with st.expander(f"{index}. {species_name}"):
            render_analysis_result(
                result,
                show_review_controls=show_review_controls,
                review_key=f"human_review_{index}",
            )

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

tab_image, tab_audio, tab_video = st.tabs(["📷 Cámara trampa", "🎙️ Audio", "🎞️ Video"])

with tab_image:
    upload = st.file_uploader("Carga una foto de cámara trampa", type=["jpg", "jpeg", "png", "webp"])
    if upload:
        st.image(upload, caption=upload.name, width="stretch")

with tab_audio:
    audio_mode = st.radio("Tipo de audio", ["Nota de campo humana", "Vocalización de ave (BirdNET beta)"], horizontal=True)
    if audio_mode.startswith("Vocalización"):
        st.caption("BirdNET está diseñado para vocalizaciones de aves. Para otras especies, registra una nota de campo humana y valida la observación de forma manual.")
    audio = st.audio_input("Graba una nota de campo")
    audio_upload = st.file_uploader("o carga un audio", type=["mp3", "wav", "m4a", "ogg"], key="audio_file")

with tab_video:
    video_upload = st.file_uploader("Carga un video de cámara trampa", type=["mp4", "mov", "avi", "webm"])
    if video_upload:
        st.video(video_upload)
        st.caption("El análisis revisa hasta 12 fotogramas y devuelve una detección por taxón distinto visible.")

st.divider()
event_date, latitude, longitude, locality = render_location_context()

if st.button("Analizar evidencia", type="primary", width="stretch"):
    evidence = upload or audio or audio_upload or video_upload
    requires_openai = bool(upload or video_upload or ((audio or audio_upload) and audio_mode == "Nota de campo humana"))
    if not evidence:
        st.error("Carga una imagen o graba/carga un audio antes de analizar.")
    elif requires_openai and not os.getenv("OPENAI_API_KEY"):
        st.error("Falta `OPENAI_API_KEY`. Agrégala a tus variables de entorno y reinicia la app.")
    else:
        context = {
            "eventDate": event_date.isoformat(),
            "decimalLatitude": latitude,
            "decimalLongitude": longitude,
            "locality": locality or None,
        }
        try:
            with st.spinner("El equipo de agentes está procesando la evidencia…"):
                if upload:
                    result = analyze_image(upload.getvalue(), upload.type or "image/jpeg", model, context)
                elif video_upload:
                    results = analyze_video(video_upload.getvalue(), video_upload.name, model, context)
                else:
                    source = audio or audio_upload
                    if audio_mode == "Vocalización de ave (BirdNET beta)":
                        result = analyze_bird_audio(source.getvalue(), source.name, context)
                    else:
                        result = analyze_audio(source.getvalue(), source.name, source.type or "audio/wav", model, context)
            results = results if video_upload else [result]
            st.session_state["analysis_results"] = results
            st.session_state["analysis_result"] = results[0]
            for index in range(9):
                review_key = "human_review" if index == 0 else f"human_review_{index}"
                st.session_state.pop(review_key, None)
                st.session_state.pop(f"{review_key}_verdict", None)
                st.session_state.pop(f"{review_key}_proposed_species", None)
                st.session_state.pop(f"{review_key}_notes", None)
            if latitude is not None and longitude is not None:
                with st.spinner("Consultando especies potenciales cercanas…"):
                    save_potential_species(
                        latitude,
                        longitude,
                        st.session_state.get("potential_radius", 10),
                        st.session_state.get("potential_group", "Todos"),
                        st.session_state.get("potential_source", "Ambas"),
                    )
                with st.spinner("Consultando perfil ambiental del punto…"):
                    save_habitat_profile(latitude, longitude, st.session_state.get("potential_radius", 10))
            st.success("Registro listo para revisión humana.")
        except Exception as error:
            st.error(f"No fue posible procesar la evidencia: {error}")

stored_results = st.session_state.get("analysis_results")
if not stored_results and st.session_state.get("analysis_result"):
    stored_results = [st.session_state["analysis_result"]]
tab_all, tab_detection, tab_species, tab_habitat = st.tabs(
    ["Todo", "Detección", "Especies cercanas", "Perfil ambiental"]
)

with tab_all:
    if stored_results:
        render_analysis_results(stored_results)
        st.caption("Las descargas están disponibles en la pestaña Detección.")
    else:
        st.info("Analiza una evidencia para ver aquí la detección, junto con el contexto ecológico disponible.")
    st.divider()
    render_potential_species_section(latitude, longitude, allow_actions=False)
    st.divider()
    render_habitat_profile_section(latitude, longitude, allow_actions=False)

with tab_detection:
    if stored_results:
        render_analysis_results(stored_results, show_review_controls=True)
        st.download_button(
            "Descargar JSON", json.dumps(stored_results, ensure_ascii=False, indent=2),
            file_name="strepitus_observations.json", mime="application/json", width="stretch",
        )
        st.download_button(
            "Descargar CSV Darwin Core", observations_to_csv(stored_results).encode("utf-8-sig"),
            file_name="strepitus_observations.csv", mime="text/csv", width="stretch",
        )
    else:
        st.info("Aún no hay una detección. Carga una evidencia y selecciona Analizar evidencia.")

with tab_species:
    render_potential_species_section(latitude, longitude, allow_actions=True)

with tab_habitat:
    render_habitat_profile_section(latitude, longitude, allow_actions=True)

st.caption("La identificación es una hipótesis asistida por IA y requiere revisión de personal capacitado.")
