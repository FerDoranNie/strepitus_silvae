"""Strepitus Silvae — field observations to Darwin Core records."""

import json
import os
from datetime import date
from html import escape
from typing import Any

import folium
import streamlit as st
from pyinaturalist import get_taxa
from streamlit_folium import st_folium

from ecological_context import (
    ICONIC_TAXA,
    gbif_nearby_summary,
    gbif_potential_species,
    gbif_species_url,
    potential_species,
    taxon_search_url,
    wikipedia_search_url,
)
from demo_samples import DemoSample, load_demo_samples, sample_by_name
from export import observations_to_csv
from habitat_context import habitat_profile
from habitat_illustration import generate_habitat_illustration, habitat_illustration_prompt
from services import analyze_audio, analyze_bird_audio, analyze_image, analyze_video
from species_context import species_reference

MODEL_OPTIONS = {
    "GPT-5.6 Sol — máxima capacidad": "gpt-5.6-sol",
    "GPT-5.6 Terra — equilibrio entre calidad y costo": "gpt-5.6-terra",
    "GPT-5.6 Luna — alto volumen y costo reducido": "gpt-5.6-luna",
}

DARWIN_CORE_COLUMNS = [
    "scientificName", "vernacularName", "individualCount", "behavior", "organismRemarks",
    "eventDate", "decimalLatitude", "decimalLongitude", "locality", "basisOfRecord", "identifiedBy",
]

SEARCH_STATE_KEYS = {
    "analysis_result", "analysis_results", "potential_species_results", "potential_species_description",
    "habitat_profile", "gbif_nearby_summary", "latitude_input", "longitude_input", "locality_input", "event_date_input",
    "event_location_map", "potential_source", "potential_group", "potential_radius",
    "image_file", "audio_recording", "audio_file", "video_file", "active_demo_sample",
    "evidence_tab_0", "audio_mode_0",
}


def t(spanish: str, english: str) -> str:
    """Return the interface language while keeping scientific payloads unchanged."""
    return english if st.session_state.get("interface_language", "English") == "English" else spanish


@st.dialog("Tutorial / Tutorial", width="large", icon=":material/menu_book:")
def show_tutorial() -> None:
    """Open a short bilingual onboarding guide without leaving the analysis flow."""
    tutorial_english, tutorial_spanish = st.tabs(
        ["English", "Español"],
        default="English" if st.session_state.get("interface_language", "English") == "English" else "Español",
        key="tutorial_language_tabs",
    )
    with tutorial_english:
        st.markdown("### From evidence to a reviewable record")
        st.markdown(
            "1. **Choose a demo** or upload a camera-trap image, video, bird vocalization, or human field note.\n"
            "2. **Set the event location** by clicking the map or entering coordinates. Demos set their own coordinates.\n"
            "3. Select **Analyze evidence**. Image, video, and human notes use your OpenAI API key; bird vocalizations use BirdNET.\n"
            "4. Review the proposed taxon, model-estimated probability, number of individuals, and the external taxonomic check when applicable.\n"
            "5. Explore nearby species and environmental context, then export the Darwin Core CSV or JSON."
        )
        st.info("Results are AI-assisted hypotheses. Review them before scientific, conservation, or regulatory use.")
    with tutorial_spanish:
        st.markdown("### De evidencia a un registro revisable")
        st.markdown(
            "1. **Elige una demo** o carga una imagen de cámara trampa, video, vocalización de ave o nota de campo humana.\n"
            "2. **Define la ubicación del evento** haciendo clic en el mapa o escribiendo coordenadas. Las demos aplican sus propias coordenadas.\n"
            "3. Selecciona **Analizar evidencia**. Imagen, video y notas humanas usan tu clave de OpenAI; las vocalizaciones de aves usan BirdNET.\n"
            "4. Revisa el taxón propuesto, la probabilidad estimada por el modelo, número de individuos y la validación taxonómica externa cuando aplique.\n"
            "5. Explora especies cercanas y contexto ambiental; después exporta el CSV o JSON Darwin Core."
        )
        st.info("Los resultados son hipótesis asistidas por IA. Revísalos antes de usos científicos, de conservación o regulatorios.")


def start_new_search() -> None:
    """Clear evidence and derived context while preserving app-level model settings."""
    st.session_state["search_nonce"] = st.session_state.get("search_nonce", 0) + 1
    for key in list(st.session_state):
        if (
            key in SEARCH_STATE_KEYS
            or key.startswith("human_review")
            or key.startswith("uploader_")
            or key.startswith("evidence_tab_")
            or key.startswith("audio_mode_")
            or key.startswith("habitat_illustration_")
        ):
            del st.session_state[key]


@st.cache_data(show_spinner=False)
def cached_demo_samples() -> list[DemoSample]:
    """Read the shipped demo catalog once; media bytes stay on disk until selected."""
    return load_demo_samples()


@st.cache_data(ttl=3600, show_spinner=False)
def cached_potential_species(latitude: float, longitude: float, radius_km: int, group: str) -> list[dict[str, Any]]:
    """Cache read-only community observations, never evidence-analysis results."""
    return potential_species(latitude, longitude, radius_km, group)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_gbif_potential_species(latitude: float, longitude: float, radius_km: int, group: str) -> list[dict[str, Any]]:
    """Cache GBIF's read-only occurrence context independently from iNaturalist."""
    return gbif_potential_species(latitude, longitude, radius_km, group)


@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def cached_gbif_nearby_summary(latitude: float, longitude: float, radius_km: int, group: str) -> dict[str, Any]:
    """Cache bounded recent-occurrence metrics for the environmental profile."""
    return gbif_nearby_summary(latitude, longitude, radius_km, group)


@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def cached_habitat_profile(latitude: float, longitude: float, radius_km: int) -> dict[str, Any]:
    """Cache lightweight terrain and OSM context for repeated map interactions."""
    return habitat_profile(latitude, longitude, radius_km)


@st.cache_data(ttl=86_400, max_entries=200, show_spinner=False)
def cached_species_reference(scientific_name: str, source_version: str) -> dict[str, Any]:
    """Cache public reference context; it never changes observation fields."""
    return species_reference(scientific_name)


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
    try:
        st.session_state["gbif_nearby_summary"] = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": min(radius_km, 1),
            "summary": cached_gbif_nearby_summary(
                latitude, longitude, min(radius_km, 1), st.session_state.get("potential_group", "Todos")
            ),
        }
    except Exception:
        st.session_state["gbif_nearby_summary"] = None


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


def matching_gbif_summary(latitude: float | None, longitude: float | None) -> dict[str, Any] | None:
    """Return nearby-record metrics only when they belong to the selected point."""
    stored = st.session_state.get("gbif_nearby_summary")
    if not stored or latitude is None or longitude is None:
        return None
    if abs(stored["latitude"] - latitude) > 0.000001 or abs(stored["longitude"] - longitude) > 0.000001:
        return None
    return stored.get("summary")


def build_habitat_map(latitude: float, longitude: float, profile: dict[str, Any]) -> folium.Map:
    """Build a read-only local map from the already-fetched habitat profile."""
    habitat_map = folium.Map(
        location=[latitude, longitude],
        zoom_start=16,
        control_scale=True,
        tiles="OpenStreetMap",
    )

    radius_m = profile["radius_m"]

    vegetation_name = profile.get("potential_vegetation", "Vegetación potencial no disponible")
    koppen_class = profile.get("koppen_class") or "—"
    folium.Circle(
        [latitude, longitude],
        radius=radius_m,
        color=profile.get("vegetation_color", "#6b7280"),
        weight=2,
        fill=True,
        fill_opacity=0.18,
        tooltip=f"Vegetación potencial: {vegetation_name}",
        popup=f"Köppen aproximado: {koppen_class}<br>Vegetación potencial: {vegetation_name}",
        name="Área y vegetación potencial",
    ).add_to(habitat_map)
    folium.Marker(
        [latitude, longitude],
        tooltip="Punto analizado",
        icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
    ).add_to(habitat_map)
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
    ).add_to(habitat_map)
    if profile.get("building_features"):
        folium.GeoJson(
            {"type": "FeatureCollection", "features": profile["building_features"]},
            name="Edificios OSM",
            style_function=lambda _: {
                "color": "#b5651d", "weight": 1, "fillColor": "#dca55b", "fillOpacity": 0.45,
            },
        ).add_to(habitat_map)
    if profile.get("road_features"):
        folium.GeoJson(
            {"type": "FeatureCollection", "features": profile["road_features"]},
            name="Vías OSM",
            style_function=lambda _: {"color": "#6c757d", "weight": 2},
        ).add_to(habitat_map)
    folium.LayerControl(collapsed=False).add_to(habitat_map)
    return habitat_map


def render_location_context() -> tuple[date, float | None, float | None, str]:
    """Render point selection and independent ecological-context lookup."""
    st.subheader(t("Contexto del evento", "Event context"))
    st.caption(t("Haz clic en el mapa o captura las coordenadas manualmente. El mapa no modifica la identificación de la evidencia.", "Click the map or enter coordinates manually. The map does not modify the evidence identification."))

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
        event_date = st.date_input(t("Fecha", "Date"), value=date.today(), key="event_date_input")
    with col2:
        st.text_input(t("Latitud (opcional)", "Latitude (optional)"), placeholder="19.4326", key="latitude_input")
    with col3:
        st.text_input(t("Longitud (opcional)", "Longitude (optional)"), placeholder="-99.1332", key="longitude_input")
    locality = st.text_input(t("Localidad (opcional)", "Locality (optional)"), placeholder=t("Reserva / estación de monitoreo", "Reserve / monitoring station"), key="locality_input")

    latitude, longitude = selected_coordinates()
    return event_date, latitude, longitude, locality


def render_potential_species_section(latitude: float | None, longitude: float | None, allow_actions: bool) -> None:
    """Render nearby-species results; filters belong only in the dedicated tab."""
    st.subheader(t("Especies potenciales cercanas", "Nearby potential species"))
    st.caption(t("Contexto de iNaturalist y/o GBIF de los últimos cinco años; no es presencia confirmada ni sustituye la evidencia.", "iNaturalist and/or GBIF context from the past five years; it is not confirmed presence and does not replace evidence."))

    if allow_actions:
        source_col, filter_col, radius_col, action_col = st.columns(4, vertical_alignment="bottom")
        with source_col:
            source = st.selectbox(
                t("Fuente", "Source"), ["Ambas", "iNaturalist", "GBIF"],
                format_func=lambda value: t("Ambas", "Both") if value == "Ambas" else value,
                key="potential_source",
            )
        with filter_col:
            group = st.selectbox(
                t("Grupo", "Group"), list(ICONIC_TAXA),
                format_func=lambda value: {
                    "Todos": t("Todos", "All"), "Aves": t("Aves", "Birds"), "Mamíferos": t("Mamíferos", "Mammals"),
                    "Reptiles": t("Reptiles", "Reptiles"), "Anfibios": t("Anfibios", "Amphibians"), "Insectos": t("Insectos", "Insects"),
                }[value],
                key="potential_group",
            )
        with radius_col:
            radius_km = st.selectbox(
                "Radio", [1, 5, 10, 25, 50], index=2,
                format_func=lambda value: f"{value} km", key="potential_radius",
            )
        with action_col:
            lookup = st.button(t("Consultar fuentes", "Query sources"), key="potential_species_button", width="stretch")

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
    st.subheader(t("Perfil ambiental del punto", "Environmental profile"))
    st.caption(t("Elevación de Copernicus DEM vía Open-Meteo; infraestructura mapeada en OpenStreetMap. El radio de infraestructura se limita a 1 km para respetar el servicio público.", "Copernicus DEM elevation via Open-Meteo; infrastructure mapped in OpenStreetMap. Infrastructure radius is limited to 1 km to respect the public service."))

    if allow_actions:
        refresh_habitat = st.button(t("Actualizar perfil ambiental", "Refresh environmental profile"), key="habitat_profile_button", width="stretch")
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
    metrics[0].metric(t("Elevación", "Elevation"), f"{profile['elevation_m']} m" if profile["elevation_m"] is not None else t("No disponible", "Unavailable"))
    metrics[1].metric(t("Relieve local", "Local relief"), f"{profile['local_relief_m']} m" if profile["local_relief_m"] is not None else t("No disponible", "Unavailable"))
    metrics[2].metric(t("Edificios mapeados", "Mapped buildings"), profile["mapped_buildings"])
    metrics[3].metric(t("Vías visualizadas", "Mapped roads"), f"{profile['mapped_road_length_km']} km")
    st.markdown(
        f"**Clima Köppen aproximado:** `{profile.get('koppen_class') or '—'}` "
        f"— {profile.get('koppen_label', 'No disponible')}"
    )
    st.markdown(f"**{t('Vegetación potencial inferida', 'Inferred potential vegetation')}:** {profile.get('potential_vegetation', t('No disponible', 'Unavailable'))}")
    st.caption(
        f"Normales climáticas: {profile.get('climate_period', '—')}. Activa la capa “Cobertura de suelo ESA WorldCover (2021)” en el control del mapa para ver cobertura observada; no equivale a vegetación potencial."
    )
    st.caption(f"Radio analizado: {profile['radius_m'] / 1000:g} km · Las capas naranja y gris son una muestra limitada de OpenStreetMap; pueden estar incompletas.")
    gbif_summary = matching_gbif_summary(latitude, longitude)
    if gbif_summary:
        st.divider()
        st.markdown(f"**{t('Registros GBIF cercanos', 'Nearby GBIF records')}**")
        st.caption("Ocurrencias georreferenciadas de los últimos cinco años en el radio del perfil. Son registros históricos de fuentes diversas, no una estimación de población ni presencia actual.")
        gbif_metrics = st.columns(4)
        gbif_metrics[0].metric("Registros revisados", gbif_summary["record_count"])
        gbif_metrics[1].metric("Especies distintas", gbif_summary["species_count"])
        gbif_metrics[2].metric("Con conteo explícito", gbif_summary["records_with_individual_count"])
        gbif_metrics[3].metric("Fecha más reciente", gbif_summary["latest_event_date"] or "No disponible")
        if gbif_summary["records_with_individual_count"]:
            st.caption(
                f"Suma reportada en los {gbif_summary['records_with_individual_count']} registros con `individualCount`: "
                f"{gbif_summary['reported_individuals']}. No equivale al número de individuos presentes hoy."
            )
        if gbif_summary["top_species"]:
            st.dataframe(
                gbif_summary["top_species"],
                hide_index=True,
                width="stretch",
                column_config={"GBIF": st.column_config.LinkColumn("Ficha GBIF", display_text="Abrir ficha")},
            )
        if not gbif_summary["sample_complete"]:
            st.caption("La consulta alcanzó el límite de la muestra; los conteos mostrados son parciales.")
    st.markdown(f"**{t('Mapa local', 'Local map')}**")
    st.caption("Activa o desactiva las capas desde el control superior derecho. Este mapa es de lectura: para cambiar el punto usa el mapa de Contexto del evento.")
    st_folium(
        build_habitat_map(latitude, longitude, profile),
        key=f"habitat_context_map_{'detail' if allow_actions else 'overview'}",
        height=460,
        returned_objects=[],
        use_container_width=True,
    )


def render_wiki_explorer_section(results: list[dict[str, Any]]) -> None:
    """Render public, evidence-adjacent reference cards instead of generic 3D models."""
    st.subheader(t("Explorador Wiki de especies", "Species Wiki Explorer"))
    st.caption("🧊 3D model — next")
    st.caption(t("Ficha pública para contextualizar la detección; no sustituye una identificación revisada por especialistas.", "Public reference cards that contextualize a detection; they do not replace expert-reviewed identification."))
    if not results:
        st.info(t("Analiza una evidencia con una especie identificada para abrir su ficha.", "Analyze evidence with an identified species to open its reference card."))
        return

    labels = [result.get("vernacularName") or result.get("scientificName") or f"Especie {index}" for index, result in enumerate(results, start=1)]
    species_tabs = st.tabs(labels)
    for index, (species_tab, result) in enumerate(zip(species_tabs, results), start=1):
        scientific_name = result.get("scientificName") or ""
        common_name = result.get("vernacularName") or scientific_name or f"Especie {index}"
        with species_tab:
            with st.spinner(t("Consultando ficha taxonómica pública…", "Retrieving public taxonomic reference…")):
                reference = cached_species_reference(scientific_name, "mediawiki-action-v2")
            conservation = reference.get("conservation_status")
            if conservation:
                st.success(f"{t('Estado de conservación registrado', 'Recorded conservation status')}: **{conservation}**")
            else:
                st.info(t("No se encontró una categoría IUCN registrada en Wikidata para este taxón.", "No IUCN category was found for this taxon in Wikidata."))

            image_col, details_col = st.columns([1, 1.2], gap="large")
            with image_col:
                if reference.get("thumbnail_url"):
                    st.image(reference["thumbnail_url"], caption=t("Imagen de referencia de Wikipedia", "Wikipedia reference image"), width="stretch")
                else:
                    st.info(t("Wikipedia no ofreció una imagen de referencia para este taxón.", "Wikipedia did not provide a reference image for this taxon."))
            with details_col:
                st.markdown(f"### *{escape(common_name)}*")
                if scientific_name:
                    st.markdown(f"*{escape(scientific_name)}*")
                probability = result.get("identificationProbability")
                if isinstance(probability, (int, float)):
                    st.caption(f"{t('Probabilidad estimada por el modelo', 'Model-estimated probability')}: {int(probability)}%")
                st.caption(f"{t('Rango taxonómico', 'Taxonomic rank')}: {reference.get('taxon_rank', t('Taxón identificado', 'Identified taxon'))}")
                st.write(reference.get("summary", "No hay resumen disponible."))
                wikipedia_url = reference.get("wikipedia_url")
                iucn_url = reference.get("iucn_url")
                links = [f"[Wikipedia]({wikipedia_url})"] if wikipedia_url else []
                if iucn_url:
                    links.append(f"[Ficha o búsqueda IUCN]({iucn_url})")
                validation = result.get("validacionExterna") or {}
                taxon_id = validation.get("idTaxonomico")
                if taxon_id:
                    links.append(f"[iNaturalist](https://www.inaturalist.org/taxa/{taxon_id})")
                if links:
                    st.markdown(" · ".join(links))
            illustration_key = f"habitat_illustration_{index}"
            latitude = result.get("decimalLatitude")
            longitude = result.get("decimalLongitude")
            profile = matching_habitat_profile(latitude, longitude) if latitude is not None and longitude is not None else None
            if st.button(
                t("Generar ilustración de hábitat", "Generate habitat illustration"),
                key=f"generate_habitat_illustration_{index}",
                icon=":material/auto_awesome:",
            ):
                if not os.getenv("OPENAI_API_KEY"):
                    st.error(t("Falta `OPENAI_API_KEY` para generar la ilustración.", "`OPENAI_API_KEY` is required to generate the illustration."))
                else:
                    prompt = habitat_illustration_prompt(
                        scientific_name=scientific_name,
                        common_name=common_name,
                        locality=result.get("locality"),
                        potential_vegetation=profile.get("potential_vegetation") if profile else None,
                        koppen_class=profile.get("koppen_class") if profile else None,
                    )
                    try:
                        with st.spinner(t("Generando ilustración bajo demanda…", "Generating illustration on demand…")):
                            st.session_state[illustration_key] = generate_habitat_illustration(prompt)
                    except Exception as error:
                        st.error(t("No fue posible generar la ilustración: ", "Could not generate the illustration: ") + str(error))
            if st.session_state.get(illustration_key):
                st.image(
                    st.session_state[illustration_key],
                    caption=t(
                        "Ilustración generada por IA: no es evidencia observacional ni confirma presencia en el sitio.",
                        "AI-generated illustration: not observational evidence and does not confirm presence at the site.",
                    ),
                    width="stretch",
                )
            st.caption(t("Wikipedia y Wikidata son fuentes comunitarias. Confirma el estado vigente directamente en IUCN antes de cualquier uso de conservación o regulación.", "Wikipedia and Wikidata are community-maintained sources. Confirm the current status directly with IUCN before conservation or regulatory use."))


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
    probability = result.get("identificationProbability")
    probability_text = f"{int(probability)}%" if isinstance(probability, (int, float)) else "—"
    common_name = escape(result.get("vernacularName") or "Sin determinar")
    scientific_name = escape(result.get("scientificName") or "Sin determinar")

    st.subheader("Resultado para revisión")
    col_species, col_count, col_confidence = st.columns(3)
    col_species.markdown(
        "<div style='font-size:.9rem; color:#606060; margin-bottom:.25rem'>Especie propuesta</div>"
        f"<div style='font-size:1.7rem; line-height:1.25'><i>{common_name}</i></div>"
        f"<div style='font-size:1rem; color:#606060; margin-top:.2rem'><i>{scientific_name}</i></div>",
        unsafe_allow_html=True,
    )
    col_count.metric("Individuos", result["individualCount"])
    col_confidence.markdown(
        f"<div style='margin-top: 0.4rem; color: {confidence_color}; font-weight: 700;'>"
        f"Confianza {confidence_label}</div>"
        f"<div style='margin-top:.35rem; font-size:1.2rem; font-weight:700'>{probability_text}</div>"
        "<div style='font-size:.78rem; color:#606060'>Probabilidad estimada por el modelo</div>",
        unsafe_allow_html=True,
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
        candidate_rows = []
        for candidate in result["bioacousticCandidates"]:
            candidate_rows.append({
                "Nombre común": candidate.get("vernacularName") or "—",
                "Nombre científico": candidate.get("scientificName") or "—",
                "Probabilidad BirdNET": f"{round(float(candidate.get('confidence', 0)) * 100)}%",
            })
        st.dataframe(candidate_rows, hide_index=True, width="stretch")

    if result.get("transcripcion"):
        with st.expander("Transcripción original"):
            st.write(result["transcripcion"])

    st.subheader("Registro Darwin Core extendido")
    st.dataframe([{key: result.get(key) for key in DARWIN_CORE_COLUMNS}], hide_index=True, width="stretch")
    with st.expander("JSON completo"):
        st.json(result)


def normalize_analysis_results(raw_results: Any) -> list[dict[str, Any]]:
    """Accept legacy single-result state as well as the current video-result list."""
    if isinstance(raw_results, dict):
        observations = raw_results.get("observations")
        if isinstance(observations, list):
            return [record for record in observations if isinstance(record, dict)]
        return [raw_results]
    if isinstance(raw_results, list):
        return [record for record in raw_results if isinstance(record, dict)]
    return []


def render_analysis_results(results: list[dict[str, Any]] | dict[str, Any], show_review_controls: bool = False) -> None:
    """Render one result or a reviewable set of distinct video detections."""
    results = normalize_analysis_results(results)
    if not results:
        st.warning("El resultado no tiene observaciones válidas para mostrar. Vuelve a ejecutar el análisis.")
        return
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
                "Probabilidad estimada": f"{result.get('identificationProbability', '—')}%" if result.get("identificationProbability") is not None else "—",
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

st.set_page_config(
    page_title="Strepitus Silvae",
    page_icon="logos_e_imagenes/strepitus_silvae_logo_svg.svg",
    layout="wide",
)
st.logo("logos_e_imagenes/strepitus_silvae_logo_svg.svg", size="large")

st.title("Strepitus Silvae")
st.caption(t("Copiloto de campo para transformar evidencia de fauna en registros Darwin Core verificables.", "Field copilot that transforms wildlife evidence into reviewable Darwin Core records."))

with st.sidebar:
    st.selectbox("Language / Idioma", ["English", "Español"], key="interface_language")
    st.header(t("Configuración", "Settings"))
    if st.button(t("Abrir tutorial", "Open tutorial"), icon=":material/menu_book:", width="stretch"):
        show_tutorial()
    env_model = os.getenv("OPENAI_MODEL", "gpt-5.6-sol")
    default_label = next((label for label, model_id in MODEL_OPTIONS.items() if model_id == env_model), None)
    selected_label = st.selectbox(
        "Modelo de análisis", list(MODEL_OPTIONS),
        index=list(MODEL_OPTIONS).index(default_label) if default_label else 0,
    )
    model = MODEL_OPTIONS[selected_label]
    if st.checkbox("Usar un identificador de modelo personalizado"):
        model = st.text_input(t("Identificador personalizado", "Custom model identifier"), value=env_model)
    st.caption(t("La clave se lee exclusivamente desde `OPENAI_API_KEY` en el entorno.", "The key is read only from `OPENAI_API_KEY` in the environment."))
    st.button(
        t("Nueva búsqueda", "New search"),
        icon=":material/restart_alt:",
        help=t("Limpia la evidencia, resultados, ubicación y contexto de la búsqueda actual.", "Clears evidence, results, location, and context from the current search."),
        on_click=start_new_search,
        width="stretch",
    )

demo_samples = cached_demo_samples()
active_demo: DemoSample | None = sample_by_name(demo_samples, st.session_state.get("active_demo_sample"))

with st.expander(t("Demos con créditos", "Credited demos"), expanded=active_demo is not None):
    if not demo_samples:
        st.info(t("No se encontraron demos locales.", "No local demos were found."))
    else:
        demo_names = [sample.name for sample in demo_samples]
        selected_demo_name = st.selectbox(
            t("Elige una evidencia de demostración", "Choose demonstration evidence"),
            demo_names,
            index=demo_names.index(active_demo.name) if active_demo else 0,
            key="demo_sample_picker",
        )
        selected_demo = sample_by_name(demo_samples, selected_demo_name)
        if selected_demo:
            type_label = {
                "image": t("imagen", "image"),
                "video": t("video", "video"),
                "audio_bird": t("vocalización de ave", "bird vocalization"),
                "audio_record": t("nota de campo", "field note"),
            }.get(selected_demo.sample_type, selected_demo.sample_type)
            st.caption(f"{t('Tipo', 'Type')}: {type_label} · {selected_demo.latitude:.5f}, {selected_demo.longitude:.5f}")
            st.caption(f"{t('Crédito', 'Credit')}: {selected_demo.citation}")
        demo_action, clear_action = st.columns(2)
        with demo_action:
            use_demo = st.button(t("Usar esta demo", "Use this demo"), key="use_demo_sample", width="stretch")
        with clear_action:
            clear_demo = st.button(t("Quitar demo", "Clear demo"), key="clear_demo_sample", disabled=active_demo is None, width="stretch")
        if use_demo and selected_demo:
            st.session_state["active_demo_sample"] = selected_demo.name
            st.session_state["latitude_input"] = f"{selected_demo.latitude:.6f}"
            st.session_state["longitude_input"] = f"{selected_demo.longitude:.6f}"
            st.session_state["locality_input"] = f"Demo: {selected_demo.name}"
            demo_tab = "audio" if selected_demo.sample_type.startswith("audio_") else selected_demo.sample_type
            demo_tab_label = {
                "image": t("📷 Cámara trampa", "📷 Camera trap"),
                "audio": "🎙️ Audio",
                "video": "🎞️ Video",
            }.get(demo_tab, t("📷 Cámara trampa", "📷 Camera trap"))
            st.session_state[f"evidence_tab_{st.session_state.get('search_nonce', 0)}"] = demo_tab_label
            if selected_demo.sample_type in {"audio_bird", "audio_record"}:
                st.session_state[f"audio_mode_{st.session_state.get('search_nonce', 0)}"] = selected_demo.sample_type
            st.rerun()
        if clear_demo:
            st.session_state.pop("active_demo_sample", None)
            st.rerun()

if active_demo:
    st.info(
        t("Demo activa: ", "Active demo: ")
        + active_demo.name
        + ". "
        + t("Sus coordenadas se aplican a esta sesión y su crédito permanece visible arriba.", "Its coordinates apply to this session and its credit remains visible above.")
    )

uploader_nonce = st.session_state.get("search_nonce", 0)
upload = audio = audio_upload = video_upload = None
tab_labels = {
    "image": t("📷 Cámara trampa", "📷 Camera trap"),
    "audio": "🎙️ Audio",
    "video": "🎞️ Video",
}
demo_tab = "audio" if active_demo and active_demo.sample_type.startswith("audio_") else (active_demo.sample_type if active_demo else "image")
tab_image, tab_audio, tab_video = st.tabs(
    list(tab_labels.values()),
    default=tab_labels.get(demo_tab, tab_labels["image"]),
    key=f"evidence_tab_{uploader_nonce}",
    on_change="rerun",
)

with tab_image:
    if active_demo and active_demo.sample_type == "image":
        upload = active_demo
        st.image(upload.getvalue(), caption=upload.name, width="stretch")
    else:
        upload = st.file_uploader(t("Carga una foto de cámara trampa", "Upload a camera-trap photo"), type=["jpg", "jpeg", "png", "webp"], key=f"uploader_image_{uploader_nonce}")
    if upload:
        if not active_demo:
            st.image(upload, caption=upload.name, width="stretch")

with tab_audio:
    field_note_label = t("Nota de campo humana", "Human field note")
    bird_audio_label = t("Vocalización de ave (BirdNET beta)", "Bird vocalization (BirdNET beta)")
    audio_mode = st.radio(
        t("Tipo de audio", "Audio type"),
        ["audio_record", "audio_bird"],
        format_func=lambda value: field_note_label if value == "audio_record" else bird_audio_label,
        horizontal=True,
        key=f"audio_mode_{uploader_nonce}",
    )
    if audio_mode == "audio_bird":
        st.caption(t("BirdNET está diseñado para vocalizaciones de aves. Para otras especies, registra una nota de campo humana y valida la observación de forma manual.", "BirdNET is designed for bird vocalizations. For other species, record a human field note and validate the observation manually."))
    if active_demo and active_demo.sample_type in {"audio_bird", "audio_record"}:
        audio_upload = active_demo
        st.audio(audio_upload.getvalue(), format=audio_upload.mime_type)
        st.caption(audio_upload.name)
    else:
        audio = st.audio_input(t("Graba una nota de campo", "Record a field note"), key=f"uploader_audio_recording_{uploader_nonce}")
        audio_upload = st.file_uploader(t("o carga un audio", "or upload an audio file"), type=["mp3", "wav", "m4a", "ogg"], key=f"uploader_audio_file_{uploader_nonce}")

with tab_video:
    if active_demo and active_demo.sample_type == "video":
        video_upload = active_demo
        st.video(video_upload.getvalue())
    else:
        video_upload = st.file_uploader(t("Carga un video de cámara trampa", "Upload a camera-trap video"), type=["mp4", "mov", "avi", "webm"], key=f"uploader_video_{uploader_nonce}")
    if video_upload:
        if not active_demo:
            st.video(video_upload)
        st.caption(t("El análisis revisa hasta 12 fotogramas y devuelve una detección por taxón distinto visible.", "Analysis reviews up to 12 frames and returns one detection per distinct visible taxon."))

st.divider()
event_date, latitude, longitude, locality = render_location_context()

if st.button(t("Analizar evidencia", "Analyze evidence"), type="primary", width="stretch"):
    evidence = upload or audio or audio_upload or video_upload
    requires_openai = bool(upload or video_upload or ((audio or audio_upload) and audio_mode == "audio_record"))
    if not evidence:
        st.error(t("Carga una imagen o graba/carga un audio antes de analizar.", "Upload an image or record/upload audio before analyzing."))
    elif requires_openai and not os.getenv("OPENAI_API_KEY"):
        st.error(t("Falta `OPENAI_API_KEY`. Agrégala a tus variables de entorno y reinicia la app.", "`OPENAI_API_KEY` is missing. Add it to your environment variables and restart the app."))
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
                    raw_result = analyze_image(upload.getvalue(), upload.type or "image/jpeg", model, context)
                elif video_upload:
                    raw_result = analyze_video(video_upload.getvalue(), video_upload.name, model, context)
                else:
                    source = audio or audio_upload
                    if audio_mode == "audio_bird":
                        raw_result = analyze_bird_audio(source.getvalue(), source.name, context)
                    else:
                        raw_result = analyze_audio(source.getvalue(), source.name, source.type or "audio/wav", model, context)
            results = normalize_analysis_results(raw_result)
            if not results:
                raise ValueError("El análisis no devolvió observaciones válidas.")
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

stored_results = normalize_analysis_results(st.session_state.get("analysis_results"))
if not stored_results:
    stored_results = normalize_analysis_results(st.session_state.get("analysis_result"))
tab_detection, tab_species, tab_habitat, tab_explorer, tab_all = st.tabs(
    [
        t("🔎 Detección", "🔎 Detection"), t("🦜 Especies cercanas", "🦜 Nearby species"),
        t("🌿 Perfil ambiental", "🌿 Environmental profile"), t("📚 Explorador Wiki", "📚 Wiki explorer"),
        t("✨ Todo", "✨ All"),
    ]
)

with tab_all:
    if stored_results:
        render_analysis_results(stored_results)
        st.caption(t("Las descargas están disponibles en la pestaña Detección.", "Downloads are available in the Detection tab."))
    else:
        st.info(t("Analiza una evidencia para ver aquí la detección, junto con el contexto ecológico disponible.", "Analyze evidence to see the detection and available ecological context here."))
    st.divider()
    render_potential_species_section(latitude, longitude, allow_actions=False)
    st.divider()
    render_habitat_profile_section(latitude, longitude, allow_actions=False)

with tab_detection:
    if stored_results:
        render_analysis_results(stored_results, show_review_controls=True)
        st.download_button(
            t("Descargar JSON", "Download JSON"), json.dumps(stored_results, ensure_ascii=False, indent=2),
            file_name="strepitus_observations.json", mime="application/json", width="stretch",
        )
        st.download_button(
            t("Descargar CSV Darwin Core", "Download Darwin Core CSV"), observations_to_csv(stored_results).encode("utf-8-sig"),
            file_name="strepitus_observations.csv", mime="text/csv", width="stretch",
        )
    else:
        st.info(t("Aún no hay una detección. Carga una evidencia y selecciona Analizar evidencia.", "There is no detection yet. Upload evidence and select Analyze evidence."))

with tab_species:
    render_potential_species_section(latitude, longitude, allow_actions=True)

with tab_habitat:
    render_habitat_profile_section(latitude, longitude, allow_actions=True)

with tab_explorer:
    render_wiki_explorer_section(stored_results)

st.caption(t("La identificación es una hipótesis asistida por IA y requiere revisión de personal capacitado.", "Identification is an AI-assisted hypothesis and requires review by qualified personnel."))
