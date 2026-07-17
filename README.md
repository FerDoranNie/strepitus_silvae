# Strepitus Silvae

**AI-assisted field-data copilot for conservation teams.** It transforms camera-trap images and spoken field notes into reviewable, Darwin Core-aligned observation records.

[Español](#español) · [English](#english)

---

## Español

### Qué hace

- Analiza evidencia de fauna para proponer especie, número de individuos, comportamiento, condición visible y presencia de personas o vehículos.
- Transcribe notas de campo y las transforma al mismo registro estructurado.
- Cuando la confianza es `medio` o `bajo`, realiza una validación taxonómica condicional mediante iNaturalist.
- Valida cada resultado con Pydantic y permite descargar JSON o CSV alineado con Darwin Core.

### Arquitectura

1. **Vision-Ecologist:** GPT-5.6 analiza fotos de cámaras trampa.
2. **Audio-Structurer:** transcripción de OpenAI seguida de GPT-5.6 estructura la nota de voz.
3. **Taxonomic Validator:** iNaturalist verifica de forma condicional identificaciones inciertas.
4. **Validación y exportación:** Pydantic protege el esquema de salida; la interfaz exporta JSON y CSV.

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
- When confidence is `medio` or `bajo`, conditionally cross-checks the taxon through iNaturalist.
- Validates each result with Pydantic and exports Darwin Core-aligned JSON or CSV.

### Architecture

1. **Vision-Ecologist:** GPT-5.6 analyzes camera-trap images.
2. **Audio-Structurer:** OpenAI transcription followed by GPT-5.6 structures the spoken note.
3. **Taxonomic Validator:** iNaturalist conditionally checks uncertain identifications.
4. **Validation and export:** Pydantic protects the output schema; the interface exports JSON and CSV.

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

## Testing

```powershell
python -m unittest discover -s tests -v
```
