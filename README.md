---
title: Strepitus Silvae
emoji: 🌿
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
fullWidth: true
short_description: Wildlife evidence to reviewable Darwin Core records.
---

# Strepitus Silvae

**AI-assisted field-data copilot for conservation teams.** It transforms camera-trap images and spoken field notes into reviewable, Darwin Core-aligned observation records.

[Español](#español) · [English](#english)

---

## Español

### Qué hace

- Analiza evidencia de fauna para proponer especie, número de individuos, comportamiento, condición visible y presencia de personas o vehículos.
- Transcribe notas de campo y las transforma al mismo registro estructurado.
- Identifica vocalizaciones de aves con BirdNET (beta) y analiza videos de cámara trampa mediante fotogramas.
- Permite seleccionar un punto en un mapa y consultar especies observadas cerca mediante iNaturalist y GBIF; es contexto comunitario, no presencia confirmada.
- Genera un perfil ambiental ligero con elevación, relieve local y edificios/vías mapeados en OpenStreetMap. Incluye una clasificación climática Köppen aproximada a partir de normales 1991–2020, una inferencia de vegetación potencial, una capa opcional de cobertura terrestre ESA WorldCover 2021 y un mapa local 2D; ninguna de ellas confirma vegetación local a escala de sitio.
- Resume registros GBIF georreferenciados cercanos de los últimos cinco años, incluyendo especies, fecha reciente y los registros que declaran `individualCount`. Es contexto histórico, no una estimación poblacional ni presencia actual.
- Incluye un Explorador Wiki de especies con imagen y resumen de Wikipedia, enlaces públicos y el estado de conservación registrado en Wikidata cuando exista.
- Puede generar bajo demanda una ilustración de hábitat con GPT Image; se etiqueta explícitamente como contenido generado por IA y no como evidencia observacional.
- Incluye demos locales seleccionables para la presentación. Cada una carga su evidencia, coordenadas y cita desde `samples/samples_for_demo/samples_directory.csv`; los créditos se muestran antes de usarla.
- Cuando la confianza es `medio` o `bajo`, realiza una validación taxonómica condicional mediante iNaturalist.
- Valida cada resultado con Pydantic y permite descargar JSON o CSV alineado con Darwin Core.

### Arquitectura

1. **Vision-Ecologist:** GPT-5.6 analiza fotos de cámaras trampa.
2. **Audio-Structurer:** transcripción de OpenAI seguida de GPT-5.6 estructura la nota de voz.
3. **Taxonomic Validator:** iNaturalist verifica de forma condicional identificaciones inciertas.
4. **Contexto ecológico:** un mapa seleccionable, iNaturalist, GBIF, un perfil ambiental 2D y un explorador de especies presentan contexto sin alterar la identificación basada en evidencia.
5. **Validación y exportación:** Pydantic protege el esquema de salida; la interfaz exporta JSON y CSV.

La interfaz permite elegir GPT-5.6 Sol (máxima capacidad), Terra (equilibrio) o Luna (alto volumen y menor costo).

### Ejecutar localmente

Consulta la guía completa de [instructions.md](instructions.md). Resumen:

```powershell
conda activate strepitus_silvae
python -m pip install -r requirements.txt
$env:OPENAI_API_KEY="tu_clave"
streamlit run app.py
```

### Desplegar en Hugging Face Spaces

El repositorio incluye la configuración para una Space Docker (`Dockerfile` y el encabezado YAML superior). Crea una Space de tipo **Docker** y agrega `OPENAI_API_KEY` en **Settings → Secrets**. Las variables no secretas opcionales son `OPENAI_MODEL`, `OPENAI_IMAGE_MODEL` y `OPENAI_IMAGE_QUALITY`. No subas `.env` ni `.streamlit/secrets.toml`.

### Uso responsable

Cada resultado es una hipótesis asistida por IA. Personal capacitado debe revisarlo antes de usarlo en decisiones científicas, regulatorias o de conservación.

### Créditos

- **Fernando Dorantes Nieto** — creador del proyecto; dirección de producto y científica, curaduría de evidencias, selección de demos, pruebas y revisión final.
- **Codex con GPT-5.6** — colaborador de desarrollo asistido por IA; apoyó el diseño técnico, la implementación, depuración, pruebas y documentación bajo la dirección de Fernando.
- **Búho de Codex** — mascota visual que acompaña la experiencia del proyecto.

### Itinerario de construcción — julio de 2026

| Día | Enfoque |
| --- | --- |
| **Miércoles 15** | Motor auditivo y checkpoint de reglas: transcripción de notas de campo, mapeo estructurado y validación de requisitos del reto. |
| **Jueves 16** | Estandarización y narrativa: esquema Pydantic/Darwin Core, exportación CSV y primer guion del pitch. |
| **Viernes 17** | Interfaz analítica: tablero Streamlit, carga de evidencia, resultados revisables y señales de validación externa. |
| **Sábado 18** | Integración end-to-end: pruebas con imágenes, audios y videos; manejo de excepciones y contexto de ubicación. |
| **Domingo 19** | Pulido basado en pruebas: detección multiespecie en video, contexto ecológico, mapas y Explorador Wiki. La grabación se reprogramó para el lunes. |
| **Lunes 20** | Documentación, despliegue Docker en Hugging Face, pulido responsive/PWA y **comienzo de la grabación del video**. |
| **Martes 21** | Entrega: verificación final del repositorio, enlace funcional, video público y formulario de Devpost. |

---

## English

### What it does

- Analyzes wildlife evidence to propose species, individual count, behavior, visible condition, and human or vehicle presence.
- Transcribes field notes and maps them to the same structured observation record.
- Identifies bird vocalizations with BirdNET (beta) and analyzes camera-trap video through sampled frames.
- Lets users select a map point and query nearby observed species through iNaturalist and GBIF; this is community context, not confirmed presence.
- Produces a lightweight environmental profile with elevation, local relief, and OpenStreetMap-mapped buildings and roads. It includes an approximate Köppen climate classification from 1991–2020 normals, inferred potential vegetation, an optional ESA WorldCover 2021 land-cover layer, and a local 2D map; none confirms site-scale local vegetation.
- Summarizes nearby georeferenced GBIF records from the past five years, including taxa, most recent date, and records that declare `individualCount`. This is historical context, not a population estimate or current-presence claim.
- Includes a Species Wiki Explorer with a Wikipedia image and summary, public links, and Wikidata-recorded conservation status when available.
- Can generate an on-demand habitat illustration with GPT Image; it is explicitly labeled as AI-generated content, not observational evidence.
- Includes selectable local demos for the presentation. Each loads its evidence, coordinates, and citation from `samples/samples_for_demo/samples_directory.csv`; the credit is shown before it is used.
- When confidence is `medio` or `bajo`, conditionally cross-checks the taxon through iNaturalist.
- Validates each result with Pydantic and exports Darwin Core-aligned JSON or CSV.

### Architecture

1. **Vision-Ecologist:** GPT-5.6 analyzes camera-trap images.
2. **Audio-Structurer:** OpenAI transcription followed by GPT-5.6 structures the spoken note.
3. **Taxonomic Validator:** iNaturalist conditionally checks uncertain identifications.
4. **Ecological context:** a selectable map, iNaturalist, GBIF, a 2D environmental profile, and species explorer provide context without changing evidence-based identification.
5. **Validation and export:** Pydantic protects the output schema; the interface exports JSON and CSV.

The interface lets users choose GPT-5.6 Sol (highest capability), Terra (balanced), or Luna (cost-sensitive high volume).

### Run locally

See the full [instructions.md](instructions.md) guide. Quick start:

```powershell
conda activate strepitus_silvae
python -m pip install -r requirements.txt
$env:OPENAI_API_KEY="your_key"
streamlit run app.py
```

### Deploy on Hugging Face Spaces

The repository includes a Docker Space configuration (`Dockerfile` and the YAML header above). Create a **Docker** Space, then add `OPENAI_API_KEY` in **Settings → Secrets**. Optional non-secret variables are `OPENAI_MODEL`, `OPENAI_IMAGE_MODEL`, and `OPENAI_IMAGE_QUALITY`. Do not upload `.env` or `.streamlit/secrets.toml`.

### Responsible use

Every result is an AI-assisted hypothesis. Qualified personnel must review it before scientific, regulatory, or conservation use.

### Credits

- **Fernando Dorantes Nieto** — project creator; product and scientific direction, evidence curation, demo selection, testing, and final review.
- **Codex with GPT-5.6** — AI-assisted development collaborator; supported technical design, implementation, debugging, testing, and documentation under Fernando's direction.
- **Codex owl** — visual mascot accompanying the project experience.

### Build itinerary — July 2026

| Day | Focus |
| --- | --- |
| **Wednesday 15** | Audio engine and rules checkpoint: field-note transcription, structured mapping, and challenge-requirement review. |
| **Thursday 16** | Standardization and narrative: Pydantic/Darwin Core schema, CSV export, and first pitch-script draft. |
| **Friday 17** | Analytical interface: Streamlit dashboard, evidence upload, reviewable results, and external-validation signals. |
| **Saturday 18** | End-to-end integration: image, audio, and video testing; exception handling and location context. |
| **Sunday 19** | Test-led polish: multi-species video detection, ecological context, maps, and the Wiki Explorer. Recording was rescheduled to Monday. |
| **Monday 20** | Documentation, Hugging Face Docker deployment, responsive/PWA polish, and **video recording begins**. |
| **Tuesday 21** | Submission: final repository check, working link, public video, and Devpost form. |

---

## OpenAI Build Week implementation

GPT-5.6 is the ecological reasoning and structured-data layer. OpenAI transcription converts field audio to text, while iNaturalist is a conditional external taxonomic verifier. Codex was used to evolve the initial Colab proof of concept into the Streamlit product, its orchestration, schema validation, CSV export, tests, and documentation.

The planned Devpost video narration and recording checklist are in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).
The hosting and final-submission sequence is in [docs/FINAL_DELIVERY_PLAN.md](docs/FINAL_DELIVERY_PLAN.md).
Third-party model and data notices are in [docs/THIRD_PARTY_NOTICES.md](docs/THIRD_PARTY_NOTICES.md).
Integration evidence and outstanding manual checks are tracked in [docs/TEST_LOG.md](docs/TEST_LOG.md).

## Testing

```powershell
python -m unittest discover -s tests -v
```
