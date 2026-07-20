"""Read-only species reference context from Wikimedia and Wikidata."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests


WIKIPEDIA_API_URL = "https://es.wikipedia.org/w/api.php"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
USER_AGENT = "StrepitusSilvae/1.0 (field-observation educational prototype)"


def _claim_value(entity: dict[str, Any], property_id: str) -> str | None:
    """Return the first simple Wikidata claim value, if present."""
    claims = entity.get("claims", {}).get(property_id, [])
    if not claims:
        return None
    datavalue = claims[0].get("mainsnak", {}).get("datavalue", {}).get("value")
    if isinstance(datavalue, dict):
        return datavalue.get("id")
    return str(datavalue) if datavalue is not None else None


def _entity_labels(ids: list[str]) -> dict[str, str]:
    """Look up Spanish labels, falling back to English, for a small item list."""
    if not ids:
        return {}
    response = requests.get(
        WIKIDATA_API_URL,
        params={
            "action": "wbgetentities",
            "ids": "|".join(ids),
            "props": "labels",
            "languages": "es|en",
            "format": "json",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=12,
    )
    response.raise_for_status()
    labels: dict[str, str] = {}
    for item_id, entity in response.json().get("entities", {}).items():
        item_labels = entity.get("labels", {})
        label = item_labels.get("es") or item_labels.get("en")
        if label:
            labels[item_id] = label.get("value", item_id)
    return labels


def _wikipedia_page(title: str) -> dict[str, Any] | None:
    """Fetch an introductory extract and Wikidata item through MediaWiki Action API."""
    response = requests.get(
        WIKIPEDIA_API_URL,
        params={
            "action": "query",
            "prop": "extracts|pageimages|pageprops|info",
            "exintro": 1,
            "explaintext": 1,
            "piprop": "thumbnail",
            "pithumbsize": 600,
            "inprop": "url",
            "redirects": 1,
            "titles": title,
            "format": "json",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=12,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    return next((page for page in pages.values() if "missing" not in page), None)


def species_reference(scientific_name: str) -> dict[str, Any]:
    """Return a conservative public reference card; network failures stay nonblocking."""
    fallback = {
        "summary": "No fue posible recuperar un resumen enciclopédico para este taxón.",
        "wikipedia_url": f"https://es.wikipedia.org/w/index.php?search={quote(scientific_name)}",
        "thumbnail_url": None,
        "wikidata_id": None,
        "taxon_rank": "Taxón identificado",
        "conservation_status": None,
        "iucn_id": None,
        "iucn_url": f"https://www.iucnredlist.org/search?query={quote(scientific_name)}",
    }
    if not scientific_name:
        return fallback
    try:
        page = _wikipedia_page(scientific_name)
        if not page:
            return fallback
        fallback.update(
            {
                "summary": page.get("extract") or fallback["summary"],
                "wikipedia_url": page.get("fullurl", fallback["wikipedia_url"]),
                "thumbnail_url": page.get("thumbnail", {}).get("source"),
                "wikidata_id": page.get("pageprops", {}).get("wikibase_item"),
            }
        )
        wikidata_id = fallback["wikidata_id"]
        if not wikidata_id:
            return fallback
        entity_response = requests.get(
            WIKIDATA_API_URL,
            params={
                "action": "wbgetentities",
                "ids": wikidata_id,
                "props": "claims",
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=12,
        )
        entity_response.raise_for_status()
        entity = entity_response.json().get("entities", {}).get(wikidata_id, {})
        conservation_id = _claim_value(entity, "P141")
        rank_id = _claim_value(entity, "P105")
        iucn_id = _claim_value(entity, "P627")
        labels = _entity_labels([item_id for item_id in (conservation_id, rank_id) if item_id])
        fallback["conservation_status"] = labels.get(conservation_id) if conservation_id else None
        fallback["taxon_rank"] = labels.get(rank_id, fallback["taxon_rank"]) if rank_id else fallback["taxon_rank"]
        fallback["iucn_id"] = iucn_id
        if iucn_id:
            fallback["iucn_url"] = f"https://www.iucnredlist.org/species/{quote(iucn_id)}"
    except (requests.RequestException, ValueError, KeyError):
        pass
    return fallback
