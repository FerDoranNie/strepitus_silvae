"""Bird vocalization identification using BirdNET's local acoustic model."""

import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any


class BioacousticAnalysisError(RuntimeError):
    """Raised when a sound recording cannot be analyzed as a bird vocalization."""


def _rows(predictions: Any) -> list[dict[str, Any]]:
    if hasattr(predictions, "to_dataframe"):
        predictions = predictions.to_dataframe()
    if hasattr(predictions, "dtype") and getattr(predictions.dtype, "names", None):
        return [
            {name: row[name].item() if hasattr(row[name], "item") else row[name] for name in predictions.dtype.names}
            for row in predictions
        ]
    if hasattr(predictions, "to_dicts"):
        return predictions.to_dicts()
    if hasattr(predictions, "to_pylist"):
        return predictions.to_pylist()
    if hasattr(predictions, "to_dict"):
        return predictions.to_dict("records")
    return list(predictions)


def _name_parts(raw_name: str) -> tuple[str, str]:
    parts = raw_name.split("_")
    if len(parts) < 2:
        return raw_name, ""
    scientific_parts = 1 if " " in parts[0] else min(2, len(parts))
    scientific = " ".join(parts[:scientific_parts])
    common = " ".join(parts[scientific_parts:])
    return scientific, common


def analyze_bird_vocalization(data: bytes, filename: str, suffix: str | None = None) -> dict[str, Any]:
    """Return BirdNET candidates for a recording; the first model load downloads official assets."""
    try:
        import birdnet
    except ImportError as error:
        raise BioacousticAnalysisError("BirdNET no está instalado. Ejecuta `pip install -r requirements.txt`.") from error

    suffix = suffix or Path(filename).suffix or ".wav"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(data)
            temp_path = temp_file.name
        model = birdnet.load("acoustic", "2.4", "tf")
        predictions = _rows(model.predict(temp_path))
    except Exception as error:
        raise BioacousticAnalysisError(f"BirdNET no pudo analizar el archivo: {error}") from error
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

    best_by_species: dict[str, float] = defaultdict(float)
    for prediction in predictions:
        raw_name = str(prediction.get("species_name", ""))
        confidence = float(prediction.get("confidence", 0))
        if raw_name and confidence > best_by_species[raw_name]:
            best_by_species[raw_name] = confidence

    candidates = []
    for raw_name, confidence in sorted(best_by_species.items(), key=lambda item: item[1], reverse=True)[:5]:
        scientific, common = _name_parts(raw_name)
        candidates.append({"scientificName": scientific, "vernacularName": common, "confidence": round(confidence, 3)})
    if not candidates:
        raise BioacousticAnalysisError("BirdNET no detectó vocalizaciones de aves en el archivo.")

    primary = candidates[0]
    confidence_level = "alto" if primary["confidence"] >= 0.70 else "medio" if primary["confidence"] >= 0.40 else "bajo"
    return {
        "scientificName": primary["scientificName"],
        "vernacularName": primary["vernacularName"],
        "individualCount": 1,
        "behavior": "vocalizando",
        "organismRemarks": "Identificación bioacústica preliminar mediante BirdNET; requiere revisión humana.",
        "identificationConfidence": confidence_level,
        "identificationProbability": round(primary["confidence"] * 100),
        "alertaHumanaOVehiculo": False,
        "bioacousticCandidates": candidates,
    }
