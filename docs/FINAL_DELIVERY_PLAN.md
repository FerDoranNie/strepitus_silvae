# Final Delivery Plan

## Saturday, July 18 — Prepare a safe demo path

- Create representative sample image/audio inputs and precomputed outputs.
- Add a **Demo mode** that never calls OpenAI or iNaturalist and does not require an API key.
- Verify the complete live path separately using the project owner's own credentials.

## Optional stretch feature — Only after Saturday tests pass

Add a small **Nearby biodiversity context** panel only if the complete image/audio flows, exports, tests, and demo mode are already stable.

- Use the record's latitude and longitude to query nearby documented taxa from iNaturalist.
- Show at most ten taxa with source, search radius, and observation-date context when available.
- Label every result as **documented nearby observations**, never as a claim that a species is currently present at the exact point.
- Do not add eBird, Three.js, a 3D simulation, or native mobile work during the hackathon.
- Remove the panel immediately if it weakens reliability or the demo timeline.

## Monday, July 20 — Publish the testable product

- Keep GitHub as the public, canonical code repository.
- Create a public Hugging Face **Docker Space** for the existing Streamlit application.
- Store `OPENAI_API_KEY` only as a Hugging Face Space secret; never commit it or expose it in the UI.
- Make Demo mode the safe public default so judges can test the application without consuming API credits.
- Test the Space URL in an incognito window and verify that sample image/audio, JSON export, and CSV export work.

## Tuesday, July 21 — Submit and verify

- Add the GitHub repository URL and public Hugging Face Space URL to Devpost.
- Include the YouTube demo URL, Codex `/feedback` Session ID, and English testing instructions.
- Re-test every submitted URL from an unauthenticated browser before submitting.

## Hosting decision

Use a Hugging Face Docker Space to host the current Streamlit app. Do not use ZeroGPU for this project: the production intelligence comes from GPT-5.6 and iNaturalist APIs, not from a local GPU model. Avoid rewriting the app in Gradio during the hackathon.
