"""Deterministic bridge from scientific taxonomy to approved visual archetypes."""

from __future__ import annotations

import csv
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from pygbif import species


CATALOG_PATH = Path(__file__).parent / "taxonomia" / "taxonomia.csv"

GROUP_FALLBACKS = {
    "aves": "bird_generic",
    "mamiferos": "mammal_generic",
    "reptiles": "reptile_generic",
    "anfibios": "amphibian_generic",
    "insectos": "insect_generic",
    "aracnidos": "arachnid_generic",
    "crustaceos": "crustacean_generic",
    "peces oseos": "fish_generic",
    "peces cartilaginosos": "fish_generic",
}

ARCHETYPE_RENDERERS = {
    "ave acuatica": "bird_waterfowl",
    "ave paseriforme": "bird_passerine",
}


def normalize(value: str | None) -> str:
    """Normalize taxon labels for accent- and case-insensitive catalog matching."""
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(character for character in decomposed if not unicodedata.combining(character)).casefold().strip()


@lru_cache(maxsize=1)
def visual_catalog() -> list[dict[str, str]]:
    """Load the user-curated taxonomy catalog once per process."""
    with CATALOG_PATH.open(encoding="utf-8-sig", newline="") as catalog_file:
        return list(csv.DictReader(catalog_file))


def renderer_for_archetype(archetype: str, group: str) -> str:
    """Map approved Spanish visual labels to stable renderer identifiers."""
    normalized_archetype = normalize(archetype)
    for phrase, renderer_id in ARCHETYPE_RENDERERS.items():
        if phrase in normalized_archetype:
            return renderer_id
    return GROUP_FALLBACKS.get(normalize(group), "wildlife_generic")


def visual_from_taxonomy(family: str | None, order: str | None, group: str | None) -> dict[str, str]:
    """Match family first, then order, then a broad-group fallback."""
    normalized_family, normalized_order, normalized_group = normalize(family), normalize(order), normalize(group)
    catalog = visual_catalog()
    row = next((entry for entry in catalog if normalized_family and normalize(entry.get("Familia")) == normalized_family), None)
    match_level = "family"
    if not row:
        row = next((entry for entry in catalog if normalized_order and normalize(entry.get("Orden")) == normalized_order), None)
        match_level = "order"
    if row:
        archetype = row.get("Arquetipo visual") or "Generic wildlife"
        catalog_group = row.get("Grupo") or group or "Unknown"
        return {
            "renderer_id": renderer_for_archetype(archetype, catalog_group),
            "archetype": archetype,
            "group": catalog_group,
            "order": row.get("Orden") or order or "",
            "family": row.get("Familia") or family or "",
            "match_level": match_level,
        }
    return {
        "renderer_id": GROUP_FALLBACKS.get(normalized_group, "wildlife_generic"),
        "archetype": "Generic fallback",
        "group": group or "Unknown",
        "order": order or "",
        "family": family or "",
        "match_level": "fallback",
    }


def resolve_visual_taxonomy(scientific_name: str) -> dict[str, str]:
    """Resolve GBIF taxonomy, then map it through the user-curated visual catalog."""
    if not scientific_name:
        return visual_from_taxonomy(None, None, None)
    try:
        # pygbif forwards unknown keyword arguments directly to requests.  Its
        # public API names this parameter ``scientificName`` (not ``name``).
        match: dict[str, Any] = species.name_backbone(scientificName=scientific_name)
        # GBIF's current backbone endpoint returns the accepted usage plus a
        # rank/name list rather than flat ``family`` and ``order`` fields.
        # Keep supporting the older flat shape exposed by prior clients.
        ranks = {
            str(item.get("rank", "")).casefold(): str(item.get("name", ""))
            for item in match.get("classification", [])
            if isinstance(item, dict)
        }
        return visual_from_taxonomy(
            match.get("family") or ranks.get("family"),
            match.get("order") or ranks.get("order"),
            match.get("class") or ranks.get("class"),
        )
    except Exception:
        return visual_from_taxonomy(None, None, None)
