# 🤖 Agentic Architecture & Workflow

**Strepitus Silvae** is not a simple wrapper around an LLM API. It is designed as a multi-agent orchestrated pipeline where specialized AI agents and external tools collaborate to process unstructured field data into a strict Darwin Core-compliant schema.

## 🧠 The Orchestrator (Python Main Flow)
The main application script acts as the orchestrator. It receives the raw data (image or audio) from the Streamlit interface, determines the correct processing pipeline, routes the data to the specialized agent, and handles the conditional logic for external validation.

## 👁️ Agent 1: The Vision-Ecologist (GPT-5.6 Vision)
* **Role:** Expert wildlife biologist and behavioral ecologist.
* **Task:** Analyzes nocturnal, blurry, or complex camera trap photos.
* **Output:** Extracts not just bounding boxes, but deep ecological context: species identification, individual count, behavioral patterns, apparent health, and human/vehicle presence (poaching alerts).
* **Constraints:** Must return a strictly formatted JSON object. It is instructed to self-evaluate its confidence level (`alto`, `medio`, `bajo`).

## 🎙️ Agent 2: The Audio-Structurer (Whisper + GPT-5.6)
* **Role:** Field data standardized parser.
* **Task:** Takes raw, noisy audio recordings from field biologists. Whisper provides the robust transcription, and a dedicated GPT-5.6 agent maps the chaotic spoken entities (coordinates, weather, species, dates) into relational data fields.
* **Output:** Darwin Core-compliant JSON.

## 🔍 Agent 3: The Taxonomic Validator (Tool Use / iNaturalist API)
* **Role:** External scientific truth-anchor.
* **Trigger:** This agent is autonomously activated by the Orchestrator *only* if Agent 1 (Vision) reports a `medio` or `bajo` confidence level.
* **Task:** Uses the `pyinaturalist` library to query the global iNaturalist database for the species name suggested by the Vision agent.
* **Output:** Confirms if the species exists, retrieves the official scientific name, its common name, and the global taxonomic ID, injecting this verified data back into the final payload.

---
*Authored by: Fernando Dorantes Nieto*