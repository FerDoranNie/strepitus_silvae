"""Validated, Darwin Core-aligned observation model."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TaxonValidation(BaseModel):
    """Taxonomic cross-check returned by iNaturalist for uncertain observations."""

    model_config = ConfigDict(extra="forbid")

    validacionExitosa: bool
    idTaxonomico: int | None = None
    nombreCientificoOficial: str | None = None
    nombreComun: str | None = None
    mensaje: str | None = None


class BioacousticCandidate(BaseModel):
    scientificName: str
    vernacularName: str
    confidence: float = Field(ge=0, le=1)


class FieldObservation(BaseModel):
    """A reviewable observation using Darwin Core terms where available."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scientificName: str = ""
    vernacularName: str = ""
    individualCount: int = Field(ge=0)
    behavior: str
    organismRemarks: str
    identificationConfidence: Literal["alto", "medio", "bajo"]
    alertaHumanaOVehiculo: bool
    eventDate: date
    decimalLatitude: float | None = Field(default=None, ge=-90, le=90)
    decimalLongitude: float | None = Field(default=None, ge=-180, le=180)
    locality: str | None = None
    basisOfRecord: Literal["MachineObservation"] = "MachineObservation"
    identifiedBy: str
    validacionExterna: TaxonValidation | None = None
    transcripcion: str | None = None
    bioacousticCandidates: list[BioacousticCandidate] | None = None
