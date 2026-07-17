"""Audio agent: transcription followed by GPT-powered field-data structuring."""

import os
from typing import Any

from openai import OpenAI


def transcribe_audio(client: OpenAI, data: bytes, filename: str, mime_type: str) -> str:
    return client.audio.transcriptions.create(
        model=os.getenv("TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"),
        file=(filename, data, mime_type),
    ).text


def structure_audio_note(
    client: OpenAI,
    data: bytes,
    filename: str,
    mime_type: str,
    model: str,
    context: dict[str, Any],
    structure: Any,
) -> tuple[dict[str, Any], str]:
    """Transcribe an audio note, then turn its entities into an observation record."""
    transcription = transcribe_audio(client, data, filename, mime_type)
    record = structure(
        f"Estructura esta nota de campo transcrita: {transcription}. Contexto conocido: {context}", model
    )
    record["transcripcion"] = transcription
    return record, transcription
