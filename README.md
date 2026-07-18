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
- Genera un perfil ambiental ligero con elevación, relieve local y edificios/vías mapeados en OpenStreetMap. Incluye una clasificación climática Köppen aproximada a partir de normales 1991–2020, una inferencia de vegetación potencial y una capa opcional de cobertura terrestre ESA WorldCover 2021; ninguna de ellas confirma vegetación local a escala de sitio.
- Cuando la confianza es `medio` o `bajo`, realiza una validación taxonómica condicional mediante iNaturalist.
- Valida cada resultado con Pydantic y permite descargar JSON o CSV alineado con Darwin Core.

### Arquitectura

1. **Vision-Ecologist:** GPT-5.6 analiza fotos de cámaras trampa.
2. **Audio-Structurer:** transcripción de OpenAI seguida de GPT-5.6 estructura la nota de voz.
3. **Taxonomic Validator:** iNaturalist verifica de forma condicional identificaciones inciertas.
4. **Contexto ecológico:** un mapa seleccionable, iNaturalist, GBIF y un perfil de terreno/infraestructura presentan contexto sin alterar la identificación basada en evidencia.
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

### Uso responsable

Cada resultado es una hipótesis asistida por IA. Personal capacitado debe revisarlo antes de usarlo en decisiones científicas, regulatorias o de conservación.

---

## English

### What it does

- Analyzes wildlife evidence to propose species, individual count, behavior, visible condition, and human or vehicle presence.
- Transcribes field notes and maps them to the same structured observation record.
- Identifies bird vocalizations with BirdNET (beta) and analyzes camera-trap video through sampled frames.
- Lets users select a map point and query nearby observed species through iNaturalist and GBIF; this is community context, not confirmed presence.
- Produces a lightweight environmental profile with elevation, local relief, and OpenStreetMap-mapped buildings and roads. It includes an approximate Köppen climate classification from 1991–2020 normals, inferred potential vegetation, and an optional ESA WorldCover 2021 land-cover layer; none confirms site-scale local vegetation.
- When confidence is `medio` or `bajo`, conditionally cross-checks the taxon through iNaturalist.
- Validates each result with Pydantic and exports Darwin Core-aligned JSON or CSV.

### Architecture

1. **Vision-Ecologist:** GPT-5.6 analyzes camera-trap images.
2. **Audio-Structurer:** OpenAI transcription followed by GPT-5.6 structures the spoken note.
3. **Taxonomic Validator:** iNaturalist conditionally checks uncertain identifications.
4. **Ecological context:** a selectable map, iNaturalist, GBIF, and terrain/infrastructure profile provide context without changing evidence-based identification.
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

### Responsible use

Every result is an AI-assisted hypothesis. Qualified personnel must review it before scientific, regulatory, or conservation use.

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
