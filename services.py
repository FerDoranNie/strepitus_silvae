"""Agent orchestration for Strepitus Silvae."""

import base64
import json
import os
from typing import Any

from openai import OpenAI
from pyinaturalist import get_taxa

from audio_structurer import structure_audio_note
from bioacoustics import analyze_bird_vocalization
from schema import FieldObservation
from video_processor import extract_sampled_frames

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


def analyze_video(data: bytes, filename: str, model: str, context: dict[str, Any]) -> dict[str, Any]:
    frame_urls = extract_sampled_frames(data, filename)
    content = [{"type": "input_text", "text": (
        f"Estos son fotogramas espaciados del mismo video de cámara trampa. Contexto conocido: {json.dumps(context)}. "
        "Genera una única observación conservadora que represente la fauna más claramente visible en el video."
    )}]
    content.extend({"type": "input_image", "image_url": frame_url} for frame_url in frame_urls)
    return _enrich(_structured([{"role": "user", "content": content}], model), context)


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
