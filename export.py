"""Portable exports for validated Strepitus Silvae observations."""

import csv
import io
from collections.abc import Iterable, Mapping
from typing import Any

from schema import FieldObservation

CSV_COLUMNS = [
    "scientificName", "vernacularName", "individualCount", "behavior", "organismRemarks",
    "identificationConfidence", "alertaHumanaOVehiculo", "eventDate", "decimalLatitude",
    "decimalLongitude", "locality", "basisOfRecord", "identifiedBy", "transcripcion",
    "taxonValidationStatus", "taxonId", "validatedScientificName", "validatedVernacularName",
]


def _row(observation: FieldObservation | Mapping[str, Any]) -> dict[str, Any]:
    model = observation if isinstance(observation, FieldObservation) else FieldObservation.model_validate(observation)
    payload = model.model_dump(mode="json")
    validation = payload.pop("validacionExterna", None) or {}
    payload["taxonValidationStatus"] = validation.get("validacionExitosa")
    payload["taxonId"] = validation.get("idTaxonomico")
    payload["validatedScientificName"] = validation.get("nombreCientificoOficial")
    payload["validatedVernacularName"] = validation.get("nombreComun")
    return {column: payload.get(column) for column in CSV_COLUMNS}


def observations_to_csv(observations: Iterable[FieldObservation | Mapping[str, Any]]) -> str:
    """Return UTF-8 CSV text with a stable, database-friendly column order."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(_row(observation) for observation in observations)
    return output.getvalue()
