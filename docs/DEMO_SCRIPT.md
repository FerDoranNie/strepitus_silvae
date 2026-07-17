# Strepitus Silvae — Devpost Demo Script

**Target duration:** 2 minutes 35 seconds  
**Language:** English (required submission material)  
**Track:** Work & Productivity

## 0:00–0:20 — The problem

**Show:** A dark camera-trap photograph and a phone recording interface with a noisy field note.

**Narration:**

> Wildlife monitoring teams collect thousands of camera-trap images and spoken field notes. Turning that messy evidence into reliable, standardized records can take hours—and uncertain identifications still need scientific review. Strepitus Silvae is an AI-assisted field-data copilot built for that bottleneck.

## 0:20–0:45 — The product

**Show:** The Streamlit home screen. Upload a camera-trap image, enter date and location, then click **Analyze evidence**.

**Narration:**

> A biologist can upload a camera-trap image or record a field note directly from a phone. The app keeps the event context—date, coordinates, and locality—next to the original evidence instead of asking the user to manually retype it later.

## 0:45–1:20 — Vision and validation agents

**Show:** Image result, including scientific name, count, behavior, confidence, and the human/vehicle alert. Use a result with medium confidence and expand the iNaturalist validation.

**Narration:**

> GPT-5.6 acts as a vision ecologist. It proposes a conservative identification, individual count, behavior, visible condition, and a safety alert for people or vehicles. It also reports confidence. When that confidence is medium or low, the orchestrator automatically activates a taxonomic cross-check against iNaturalist and preserves the verification result in the final record.

## 1:20–1:50 — Audio workflow

**Show:** Upload or record a noisy field note. Open the transcription panel and then the generated record.

**Narration:**

> For spoken notes, the audio agent first creates a transcription, then GPT-5.6 maps the unstructured language into the same validated observation schema. Image and audio therefore become comparable records instead of separate manual workflows.

## 1:50–2:15 — Standardized, reviewable output

**Show:** The JSON panel and both download buttons. Open the downloaded CSV briefly.

**Narration:**

> Before export, Pydantic validates the record against our Darwin Core-aligned schema. The team can download reviewable JSON or CSV ready for a scientific database. This is intentionally AI-assisted: the interface states that trained staff must review every record before it is used for conservation decisions.

## 2:15–2:35 — How OpenAI tools were used and close

**Show:** A simple architecture slide: evidence → GPT-5.6 / transcription → validation → Darwin Core export. Then show the repository README.

**Narration:**

> I used Codex to turn an initial Colab prototype into a runnable Streamlit product: its agent orchestration, Pydantic validation, CSV export, tests, and documentation. GPT-5.6 powers the ecological interpretation and the structured field-data extraction. Strepitus Silvae helps conservation teams spend less time formatting data and more time protecting wildlife.

## Recording checklist

- Use only evidence you own or are authorized to show.
- Keep the final YouTube video public and under three minutes.
- Record desktop at readable zoom; use one prepared image and one prepared audio note.
- Avoid copyrighted music and third-party logos.
- Ensure the UI result matches the claims in the narration.
