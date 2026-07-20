"""Read-only ecological context queries for a selected field location."""

from datetime import date, timedelta
from math import cos, pi, sin
from typing import Any
from urllib.parse import quote_plus

from pygbif import occurrences
from pyinaturalist import get_observation_species_counts


ICONIC_TAXA = {
    "Todos": None,
    "Aves": "Aves",
    "Mamíferos": "Mammalia",
    "Reptiles": "Reptilia",
    "Anfibios": "Amphibia",
    "Insectos": "Insecta",
}

GBIF_CLASSES = {
    "Todos": None,
    "Aves": "Aves",
    "Mamíferos": "Mammalia",
    "Reptiles": "Reptilia",
    "Anfibios": "Amphibia",
    "Insectos": "Insecta",
}


def potential_species(
    latitude: float,
    longitude: float,
    radius_km: int = 10,
    group: str = "Todos",
    limit: int = 15,
) -> list[dict[str, Any]]:
    """Return recent, research-grade iNaturalist taxa near a point.

    These are community observations near the point, not proof that a species is
    currently present or a prior for overriding evidence-based identification.
    """
    if group not in ICONIC_TAXA:
        raise ValueError(f"Grupo no compatible: {group}")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Las coordenadas están fuera de rango.")

    response = get_observation_species_counts(
        lat=latitude,
        lng=longitude,
        radius=radius_km,
        iconic_taxa=ICONIC_TAXA[group],
        quality_grade="research",
        captive=False,
        d1=(date.today() - timedelta(days=365 * 5)).isoformat(),
        per_page=limit,
        locale="es",
    )

    records = response.get("results", []) if isinstance(response, dict) else []
    return [species_row(record) for record in records]


def species_row(record: dict[str, Any]) -> dict[str, Any]:
    """Reduce an iNaturalist species-count response to UI-safe values."""
    taxon = record.get("taxon", {})
    scientific_name = taxon.get("name", "Sin determinar")
    taxon_id = taxon.get("id")
    return {
        "Nombre científico": scientific_name,
        "Nombre común": taxon.get("preferred_common_name") or "—",
        "Observaciones": record.get("count", 0),
        "Grupo": taxon.get("iconic_taxon_name") or "—",
        "Fuente": "iNaturalist",
        "Ficha taxonómica": f"https://www.inaturalist.org/taxa/{taxon_id}" if taxon_id else taxon_search_url(scientific_name),
        "Wikipedia": wikipedia_search_url(scientific_name),
    }


def gbif_potential_species(
    latitude: float,
    longitude: float,
    radius_km: int = 10,
    group: str = "Todos",
    limit: int = 15,
) -> list[dict[str, Any]]:
    """Aggregate recent georeferenced GBIF records near a selected point."""
    if group not in GBIF_CLASSES:
        raise ValueError(f"Grupo no compatible: {group}")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Las coordenadas están fuera de rango.")

    response = occurrences.search(
        geometry=radius_polygon_wkt(latitude, longitude, radius_km),
        year=f"{date.today().year - 5},{date.today().year}",
        hasCoordinate=True,
        hasGeospatialIssue=False,
        limit=300,
        timeout=20,
    )
    return aggregate_gbif_records(response.get("results", []), group, limit)


def gbif_nearby_summary(
    latitude: float,
    longitude: float,
    radius_km: int = 1,
    group: str = "Todos",
) -> dict[str, Any]:
    """Summarize recent GBIF occurrences without treating them as a population estimate."""
    if group not in GBIF_CLASSES:
        raise ValueError(f"Grupo no compatible: {group}")
    response = occurrences.search(
        geometry=radius_polygon_wkt(latitude, longitude, radius_km),
        year=f"{date.today().year - 5},{date.today().year}",
        hasCoordinate=True,
        hasGeospatialIssue=False,
        limit=300,
        timeout=20,
    )
    return summarize_gbif_nearby_records(response.get("results", []), group, response.get("endOfRecords", True))


def summarize_gbif_nearby_records(
    records: list[dict[str, Any]], group: str, end_of_records: bool = True
) -> dict[str, Any]:
    """Build UI-safe metrics from an occurrence sample and preserve their meaning."""
    expected_class = GBIF_CLASSES[group]
    filtered = [record for record in records if not expected_class or record.get("class") == expected_class]
    species: dict[str, int] = {}
    event_dates: list[str] = []
    records_with_count = 0
    reported_individuals = 0.0
    for record in filtered:
        scientific_name = record.get("species") or record.get("scientificName")
        if scientific_name:
            species[scientific_name] = species.get(scientific_name, 0) + 1
        event_date = record.get("eventDate")
        if isinstance(event_date, str) and event_date:
            event_dates.append(event_date)
        try:
            individual_count = float(record.get("individualCount"))
        except (TypeError, ValueError):
            continue
        if individual_count > 0:
            records_with_count += 1
            reported_individuals += individual_count
    return {
        "record_count": len(filtered),
        "species_count": len(species),
        "latest_event_date": max(event_dates) if event_dates else None,
        "records_with_individual_count": records_with_count,
        "reported_individuals": round(reported_individuals) if reported_individuals.is_integer() else round(reported_individuals, 1),
        "sample_complete": bool(end_of_records),
        "top_species": [
            {"Especie": name, "Registros": count, "GBIF": gbif_species_url(None, name)}
            for name, count in sorted(species.items(), key=lambda item: item[1], reverse=True)[:8]
        ],
    }


def radius_polygon_wkt(latitude: float, longitude: float, radius_km: int, points: int = 24) -> str:
    """Create a small WKT search polygon around a point for the GBIF API."""
    latitude_delta = radius_km / 111.32
    longitude_delta = radius_km / max(111.32 * cos(latitude * pi / 180), 0.01)
    coordinates = []
    for index in range(points + 1):
        angle = 2 * pi * index / points
        lon = longitude + longitude_delta * cos(angle)
        lat = latitude + latitude_delta * sin(angle)
        coordinates.append(f"{lon:.6f} {lat:.6f}")
    return f"POLYGON(({', '.join(coordinates)}))"


def aggregate_gbif_records(records: list[dict[str, Any]], group: str, limit: int) -> list[dict[str, Any]]:
    """Group GBIF occurrences by species while preserving transparent source data."""
    expected_class = GBIF_CLASSES[group]
    taxa: dict[str, dict[str, Any]] = {}
    for record in records:
        if expected_class and record.get("class") != expected_class:
            continue
        scientific_name = record.get("species") or record.get("scientificName")
        if not scientific_name:
            continue
        row = taxa.setdefault(
            scientific_name,
            {
                "Nombre científico": scientific_name,
                "Nombre común": record.get("vernacularName") or "—",
                "Observaciones": 0,
                "Grupo": record.get("class") or record.get("kingdom") or "—",
                "Fuente": "GBIF",
                "Ficha taxonómica": gbif_species_url(record.get("speciesKey"), scientific_name),
                "Wikipedia": wikipedia_search_url(scientific_name),
            },
        )
        row["Observaciones"] += 1
    return sorted(taxa.values(), key=lambda row: row["Observaciones"], reverse=True)[:limit]


def taxon_search_url(scientific_name: str) -> str:
    return f"https://www.inaturalist.org/taxa/search?q={quote_plus(scientific_name)}"


def gbif_species_url(species_key: Any, scientific_name: str) -> str:
    if species_key:
        return f"https://www.gbif.org/species/{species_key}"
    return f"https://www.gbif.org/species/search?q={quote_plus(scientific_name)}"


def wikipedia_search_url(scientific_name: str) -> str:
    return f"https://es.wikipedia.org/w/index.php?search={quote_plus(scientific_name)}"
