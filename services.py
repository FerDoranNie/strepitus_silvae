"""Agent orchestration for Strepitus Silvae."""

import base64
import json
import os
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv
from pyinaturalist import get_taxa

from audio_structurer import structure_audio_note
from bioacoustics import analyze_bird_vocalization
from schema import FieldObservation
from video_processor import extract_sampled_frames

load_dotenv()

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "scientificName": {"type": "string"}, "vernacularName": {"type": "string"},
        "individualCount": {"type": "integer", "minimum": 0}, "behavior": {"type": "string"},
        "organismRemarks": {"type": "string"}, "identificationConfidence": {"type": "string", "enum": ["alto", "medio", "bajo"]},
        "alertaHumanaOVehiculo": {"type": "boolean"},
    },
    "required": ["scientificName", "vernacularName", "individualCount", "behavior", "organismRemarks", "identificationConfidence", "alertaHumanaOVehiculo"],
}

VIDEO_MULTI_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "observations": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "items": SCHEMA,
        },
    },
    "required": ["observations"],
}

INSTRUCTIONS = """Eres un biólogo especialista en conservación en América Latina. Extrae una observación de fauna.
No inventes especies: si no es identificable, usa el taxón más conservador posible y confianza bajo.
scientificName debe ser nombre científico, o cadena vacía si no puede inferirse. vernacularName puede ser cadena vacía.
organismRemarks debe describir condición física visible o decir que no es evaluable. La respuesta debe cumplir el esquema."""


def _client() -> OpenAI:
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _structured(input_data: Any, model: str) -> dict[str, Any]:
    response = _client().responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=input_data,
        text={"format": {"type": "json_schema", "name": "field_observation", "strict": True, "schema": SCHEMA}},
    )
    return json.loads(response.output_text)


def _structured_video(input_data: Any, model: str) -> list[dict[str, Any]]:
    """Request a bounded set of distinct observations from one camera-trap video."""
    response = _client().responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=input_data,
        text={"format": {"type": "json_schema", "name": "video_observations", "strict": True, "schema": VIDEO_MULTI_SCHEMA}},
    )
    return json.loads(response.output_text)["observations"]


def _enrich(record: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    record.update({key: value for key, value in context.items() if value is not None})
    record["basisOfRecord"] = "MachineObservation"
    record["identifiedBy"] = "Strepitus Silvae (AI-assisted; human review required)"
    if record["identificationConfidence"] in {"medio", "bajo"}:
        record["validacionExterna"] = validate_taxon(record["scientificName"] or record["vernacularName"])
    return FieldObservation.model_validate(record).model_dump(mode="json")


def analyze_image(data: bytes, mime_type: str, model: str, context: dict[str, Any]) -> dict[str, Any]:
    encoded = base64.b64encode(data).decode("utf-8")
    input_data = [{"role": "user", "content": [
        {"type": "input_text", "text": f"Analiza esta fotografía de cámara trampa. Contexto conocido: {json.dumps(context)}."},
        {"type": "input_image", "image_url": f"data:{mime_type};base64,{encoded}"},
    ]}]
    return _enrich(_structured(input_data, model), context)


def analyze_audio(data: bytes, filename: str, mime_type: str, model: str, context: dict[str, Any]) -> dict[str, Any]:
    record, _ = structure_audio_note(_client(), data, filename, mime_type, model, context, _structured)
    return _enrich(record, context)


def analyze_bird_audio(data: bytes, filename: str, context: dict[str, Any]) -> dict[str, Any]:
    return _enrich(analyze_bird_vocalization(data, filename), context)


def _deduplicate_video_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge repeated appearances of the same taxon before Darwin Core validation."""
    unique: dict[str, dict[str, Any]] = {}
    confidence_rank = {"bajo": 0, "medio": 1, "alto": 2}
    for record in records:
        scientific_name = record.get("scientificName", "").strip().casefold()
        common_name = record.get("vernacularName", "").strip().casefold()
        key = scientific_name or common_name or f"unknown-{len(unique)}"
        current = unique.get(key)
        if current is None:
            unique[key] = dict(record)
            continue
        current["individualCount"] = max(current["individualCount"], record["individualCount"])
        current["alertaHumanaOVehiculo"] = current["alertaHumanaOVehiculo"] or record["alertaHumanaOVehiculo"]
        if confidence_rank[record["identificationConfidence"]] > confidence_rank[current["identificationConfidence"]]:
            current.update(record)
    return list(unique.values())


def analyze_video(data: bytes, filename: str, model: str, context: dict[str, Any]) -> list[dict[str, Any]]:
    """Analyze key frames and return one conservative record per distinct taxon."""
    frame_urls = extract_sampled_frames(data, filename, sample_count=12)
    content = [{"type": "input_text", "text": (
        f"Estos son 12 fotogramas espaciados del mismo video de cámara trampa. Contexto conocido: {json.dumps(context)}. "
        "Devuelve una observación por cada taxón distinto que sea claramente visible en al menos un fotograma. "
        "No devuelvas la misma especie más de una vez: consolida sus apariciones y usa el máximo número de individuos visibles simultáneamente, no una suma del video. "
        "No inventes especies; si el animal no permite identificación, usa el taxón más conservador posible y confianza baja. "
        "Es preferible una lista corta y sustentada a incluir candidatos dudosos."
    )}]
    content.extend({"type": "input_image", "image_url": frame_url} for frame_url in frame_urls)
    records = _deduplicate_video_records(_structured_video([{"role": "user", "content": content}], model))
    return [_enrich(record, context) for record in records]


def validate_taxon(query: str) -> dict[str, Any]:
    if not query:
        return {"validacionExitosa": False, "mensaje": "No hubo taxón para validar."}
    try:
        results = get_taxa(q=query, rank=["species", "subspecies"]).get("results", [])
        if not results:
            return {"validacionExitosa": False, "mensaje": "Sin coincidencias en iNaturalist."}
        taxon = results[0]
        return {"validacionExitosa": True, "idTaxonomico": taxon.get("id"), "nombreCientificoOficial": taxon.get("name"), "nombreComun": taxon.get("preferred_common_name")}
    except Exception as error:
        return {"validacionExitosa": False, "mensaje": f"No se pudo consultar iNaturalist: {error}"}
