# Third-party notices

## BirdNET

The optional **BirdNET beta** feature uses the `birdnet` Python package to identify bird vocalizations.

- Source code: MIT License.
- Acoustic model weights: CC BY-NC-SA 4.0.
- Citation: Kahl, S. et al. (2021), *BirdNET: A deep learning solution for avian diversity monitoring*, Ecological Informatics 61, 101236.

Before commercial deployment, distribution, or any use beyond the license's scope, the project owner must review the BirdNET model license and obtain any required permission. The feature is presented as an AI-assisted, human-review-required beta.

## iNaturalist

iNaturalist is used only for conditional taxonomic cross-checking. Any data returned by its API remains subject to iNaturalist's applicable terms and licenses.

## GBIF

GBIF provides nearby georeferenced occurrence context, including any publisher-supplied `individualCount` values. These are historical occurrence records, not a population estimate or confirmation of present-day occurrence. Dataset-level citation and licensing requirements apply to any reuse beyond the interface summary.

## Environmental context

- **Open-Meteo** provides elevation and daily historical climate values used to calculate 1991–2020 monthly normals and an approximate Köppen climate class. Open-Meteo and its underlying sources must be attributed according to their terms.
- **OpenStreetMap / Overpass** provides mapped buildings and roads; data coverage is incomplete and subject to OpenStreetMap attribution requirements.
- **ESA WorldCover 2021** is offered as an optional visual land-cover WMS layer. Attribution in the map is: “© ESA WorldCover 2021 / Copernicus Sentinel data”. It is land cover, not a field validation of vegetation.

## Species explorer

- **Wikipedia / MediaWiki Action API** supplies an optional encyclopedic summary and thumbnail for a detected taxon. Content remains subject to the applicable Wikimedia licenses and attribution requirements.
- **Wikidata** is used as a convenience reference for the recorded conservation-status property and IUCN taxon identifier when available. Its values can be incomplete or out of date; the interface links to IUCN for confirmation and must not be used as an authoritative conservation assessment.
- Any future `.glb` species model must be manually reviewed for the correct taxon and a license compatible with this project before being added to `CURATED_GLB_MODELS`. Unverified third-party 3D assets are intentionally not loaded.

## OpenAI

OpenAI APIs power the image, video-frame, and spoken-field-note flows. Use is subject to the applicable OpenAI terms and usage policies.
