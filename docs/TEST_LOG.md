# Integration test log

## 2026-07-18

| Flow | Input | Expected / source | Result | Status |
| --- | --- | --- | --- | --- |
| Bird vocalization | `XC1093057 - Melodious Blackbird - Dives dives.wav` | *Dives dives* / Melodious Blackbird (Xeno-canto XC1093057) | BirdNET returned *Dives dives* with confidence 1.000 and a valid Darwin Core-aligned record with coordinates and date. | Pass |
| Image | `columbina_passerina_1.jpeg` | Filename suggests *Columbina passerina*, but provenance is not recorded. | GPT-5.6 Luna returned *Columbina inca* / Inca Dove with high confidence. Visual review is compatible with Inca Dove. | Needs source/provenance confirmation |
| Video extraction | Generated three-frame AVI fixture | Three usable JPEG frame data URLs. | Frame extractor returned three valid JPEG data URLs. | Pass |
| Human spoken field note | `Grabacion prueba notas.m4a` | Spoken note identifies a quetzal, tapir tracks, El Triunfo Reserve, 12 July 2026 at 13:00. | Transcription and structured record returned *Pharomachrus mocinno* / Quetzal with medium confidence; iNaturalist validated the taxon. User-supplied sidebar context deliberately overrides the event date and locality in this test. | Pass; verify real context before export |
| Camera-trap video | `tayras_colombia_savig_nature_09260016.mp4` | Filename suggests tayra footage from Colombia. | Six sampled frames produced *Eira barbara* / tayra, one individual, high confidence. | Pass; confirm source licence before public demo use |
| eBird photo | `my_ebird_photos/photo_2025-12-22_22-50-34.jpg` | User-provided eBird photo; geographic metadata was not supplied to the test. | GPT-5.6 Luna returned *Aythya collaris* / Ring-necked Duck with medium confidence; iNaturalist validated the taxon. | Pass; retain attribution and licence information |
| Ecological context | iNaturalist query at 19.4326, -99.1332; 5 km; Aves | Recent research-grade community observations. | Returned *Columbina inca*, *Passer domesticus*, and *Quiscalus mexicanus* with observation counts. Streamlit render test also passed. | Pass |
| Ecological context (GBIF) | GBIF query at 19.4326, -99.1332; ~5 km; Mamíferos | Recent georeferenced occurrence records aggregated by species. | Returned *Sciurus aureogaster* (17 records) and *Bassariscus astutus* (1 record), clearly labelled as GBIF. | Pass |
| Streamlit state | Simulated analysis result followed by `Consultar fuentes` rerun | Analysis result remains visible after any context-query interaction. | `analysis_result` persisted in Streamlit session state and remained rendered after the button click. | Pass |
| Habitat profile | Open-Meteo + OSM/Overpass at 19.4326, -99.1332; 1 km | Elevation, local relief, OSM building count and road-layer sample. | Returned 2,230 m elevation, 13 m local relief, 3,249 mapped buildings and a visible road sample. | Pass; OSM completeness varies by location |
| Map and links UX | Existing Streamlit session result followed by map/context rendering | Immediate point feedback and visible external links for every potential species. | Map uses a client-side click marker plus a controlled rerun; a regression test confirmed GBIF and Wikipedia links are backfilled and rendered for prior session rows. | Pass |
| Climate and vegetation context | Open-Meteo historical normals at 20.2114, -87.4654 | Köppen approximation plus a clearly separated potential-vegetation label. | Returned `Aw` (tropical with dry season) and “Sabana y bosque tropical estacional”; ESA WorldCover 2021 is available as an optional map layer. | Pass; climatic inference is not site-scale vegetation confirmation |
| Species reference context | *Aythya affinis* / Lesser Scaup | Wikipedia summary, Wikidata taxon rank and IUCN reference when available. | MediaWiki Action API returned an extract and thumbnail; Wikidata returned rank `especie`, IUCN-linked status “especie bajo preocupación menor”, and IUCN ID `22680402`. | Pass; verify the current IUCN assessment before conservation use |
| GBIF environmental summary | Simulated recent, georeferenced bird records within profile radius | Counts must remain occurrence-context metrics, not population estimates. | Unit test returned 3 records, 2 taxa, 2 records with explicit `individualCount`, and a reported-count sum of 5; the UI labels this distinction. | Pass; perform live per-location check before demo |

## Remaining manual tests

- Public app interface: complete each flow from Streamlit, including JSON and CSV downloads.
- Map interaction: select a point and confirm that coordinates are populated before querying nearby species.
- Environmental profile: refresh a real selected point and confirm its GBIF occurrence summary, map layers, and explicit-count wording.
- Species Wiki Explorer: confirm the conservation status appears above the reference image and that each external reference link opens correctly.
- Review every medium-confidence result and confirm any image/video source licence and attribution before publishing it.

## Rule for prompt changes

Do not change prompts until a repeated error is observed against a known, correctly attributed test sample.
