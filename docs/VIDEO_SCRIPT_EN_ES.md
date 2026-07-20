# Strepitus Silvae — Video Script / Guion de video

**Target duration / Duración objetivo:** 2:40–2:55  
**Submission narration / Narración de entrega:** English  
**Spanish version / Versión en español:** rehearsal, local presentation, or subtitles

> Keep the English narration for the submission. The Spanish version mirrors the same shots and timing.

---

## 0:00–0:18 — Problem / Problema

**Show / Mostrar:** A camera-trap demo or a field-note demo, then the Strepitus Silvae home screen.

### English

> Wildlife monitoring teams receive camera-trap images, videos, and spoken field notes in many formats. Converting that evidence into structured records takes time, and uncertain identifications still require expert review. Strepitus Silvae is an AI-assisted field-data copilot designed for that workflow.

### Español

> Los equipos de monitoreo de fauna reciben imágenes y videos de cámaras trampa, así como notas de campo habladas, en muchos formatos. Convertir esa evidencia en registros estructurados toma tiempo, y las identificaciones inciertas todavía requieren revisión experta. Strepitus Silvae es un copiloto de datos de campo asistido por IA diseñado para ese flujo.

---

## 0:18–0:40 — Start with evidence / Comenzar con evidencia

**Show / Mostrar:** Open **Credited demos**, choose one sample, press **Use this demo**, and show that the correct Image, Audio, or Video tab opens automatically. Briefly show the displayed credit and coordinates.

### English

> A user can upload evidence or select a credited demo. The app routes each demo to the right evidence workflow and carries its coordinates and attribution into the session. For field work, users can also enter a locality or select a point directly on the map.

### Español

> La persona usuaria puede cargar evidencia o elegir una demo con crédito. La app dirige cada demo al flujo correcto y conserva sus coordenadas y atribución durante la sesión. Para trabajo de campo, también se puede escribir una localidad o elegir un punto directamente en el mapa.

---

## 0:40–1:12 — Evidence analysis and review / Análisis y revisión de evidencia

**Show / Mostrar:** Press **Analyze evidence**. Show common name, scientific name, probability, confidence level, individual count, and the human/vehicle alert. If available, open the iNaturalist validation card.

### English

> GPT-5.6 acts as a vision ecologist for images and sampled video frames. It proposes a taxon, the maximum visible individual count, behavior, visible condition, and a human-or-vehicle alert. The result displays both a confidence level and a model-estimated probability. These are review signals, not scientific confirmation. When confidence is medium or low, the workflow also requests a taxonomic cross-check from iNaturalist.

### Español

> GPT-5.6 actúa como ecólogo visual para imágenes y fotogramas de video. Propone un taxón, el máximo número de individuos visibles, comportamiento, condición visible y una alerta de personas o vehículos. El resultado muestra tanto un nivel de confianza como una probabilidad estimada por el modelo. Son señales para revisión, no confirmación científica. Cuando la confianza es media o baja, el flujo también solicita una validación taxonómica en iNaturalist.

---

## 1:12–1:35 — Audio workflows / Flujos de audio

**Show / Mostrar:** Switch to Audio. Show BirdNET on a bird vocalization demo, then briefly show a human field note and its transcription.

### English

> Bird vocalizations can be analyzed with BirdNET. Human field notes follow a different path: OpenAI transcription first converts speech into text, and GPT-5.6 structures that text into the same observation schema. This keeps image, video, and audio evidence comparable without manual reformatting.

### Español

> Las vocalizaciones de aves pueden analizarse con BirdNET. Las notas de campo humanas siguen una ruta distinta: primero, la transcripción de OpenAI convierte la voz a texto; después GPT-5.6 estructura ese texto en el mismo esquema de observación. Así, imagen, video y audio se mantienen comparables sin reformateo manual.

---

## 1:35–2:02 — Context and Wiki Explorer / Contexto y Explorador Wiki

**Show / Mostrar:** Select a map point, then show nearby species, the environmental profile, and the Wiki Explorer. Keep the conservation-status banner visible at the top.

### English

> Coordinates unlock context without changing the evidence-based identification. The app can show nearby community and GBIF records, terrain and mapped infrastructure, approximate climate, and inferred potential vegetation. The Wiki Explorer then presents public reference material: a Wikipedia image and summary, public links, and the conservation status recorded in Wikidata. These sources are contextual and must still be checked for conservation decisions.

### Español

> Las coordenadas desbloquean contexto sin modificar la identificación basada en evidencia. La app puede mostrar registros cercanos de la comunidad y de GBIF, terreno e infraestructura mapeada, clima aproximado y vegetación potencial inferida. El Explorador Wiki presenta entonces material público de referencia: imagen y resumen de Wikipedia, enlaces públicos y el estado de conservación registrado en Wikidata. Estas fuentes dan contexto y aún deben verificarse para decisiones de conservación.

---

## 2:02–2:17 — Optional habitat illustration / Ilustración opcional de hábitat

**Show / Mostrar:** In the Wiki Explorer, press **Generate habitat illustration** once. Show the generated image and its warning label.

### English

> This optional button generates a habitat illustration only when the user requests it. With coordinates, it uses the available environmental context; without coordinates, it creates only a neutral natural setting for the detected species. The app labels it clearly as AI-generated illustration, not observational evidence and not proof of occurrence.

### Español

> Este botón opcional genera una ilustración de hábitat solo cuando la persona usuaria la solicita. Con coordenadas, utiliza el contexto ambiental disponible; sin coordenadas, crea únicamente un entorno natural neutro para la especie detectada. La app la etiqueta claramente como ilustración generada por IA, no como evidencia observacional ni prueba de presencia.

---

## 2:17–2:42 — Export and responsible use / Exportación y uso responsable

**Show / Mostrar:** Open the Darwin Core table, JSON, and CSV download button. End on README or architecture graphic.

### English

> Before export, Pydantic validates every record against a Darwin Core-aligned schema. Teams can download reviewable JSON or CSV for their scientific databases. I used Codex to evolve the prototype into this tested Streamlit workflow: orchestration, validation, export, demos, and documentation. Strepitus Silvae does not replace field expertise. It helps conservation teams spend less time formatting evidence and more time reviewing it responsibly.

### Español

> Antes de exportar, Pydantic valida cada registro contra un esquema alineado con Darwin Core. Los equipos pueden descargar JSON o CSV revisables para sus bases de datos científicas. Usé Codex para evolucionar el prototipo hacia este flujo probado en Streamlit: orquestación, validación, exportación, demos y documentación. Strepitus Silvae no reemplaza la experiencia de campo. Ayuda a los equipos de conservación a dedicar menos tiempo a formatear evidencia y más tiempo a revisarla responsablemente.

---

## Recording checklist / Lista de grabación

- Use a prepared demo with visible credits and an analysis result ready to show.
- Generate one habitat illustration before recording if API cost or latency is a concern.
- Keep the English version under three minutes and make the final video public.
- Do not claim that AI confidence, a generated illustration, nearby records, or a Wikipedia entry confirms presence.
- Zoom the browser to keep labels, conservation status, and the Darwin Core export readable.
