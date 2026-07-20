"""On-demand, clearly labeled habitat illustrations for a detected taxon."""

from __future__ import annotations

import base64
import os
from typing import Any

from openai import OpenAI


def habitat_illustration_prompt(
    scientific_name: str,
    common_name: str,
    locality: str | None = None,
    potential_vegetation: str | None = None,
    koppen_class: str | None = None,
) -> str:
    """Describe an educational scene without claiming it documents the event."""
    species = scientific_name or common_name or "the detected wildlife taxon"
    common = f" ({common_name})" if common_name and common_name != scientific_name else ""
    if locality or potential_vegetation or koppen_class:
        context = (
            f"Illustrative environmental context only: locality {locality or 'not provided'}; "
            f"inferred potential vegetation {potential_vegetation or 'not available'}; "
            f"approximate Köppen climate {koppen_class or 'not available'}."
        )
    else:
        context = "No location is available: use a neutral, plausible natural setting without implying a geographic location."
    return (
        f"Create a single editorial natural-history illustration of {species}{common} in a plausible habitat. "
        f"{context} Show only this one focal species; do not add other animal species, people, vehicles, signs, maps, labels, text, logos, watermarks, or interface elements. "
        "Use a detailed but clearly illustrative field-guide style, with anatomically cautious proportions. "
        "This is a conceptual habitat illustration, not a camera-trap photograph and not proof that the species occurred at this site."
    )


def generate_habitat_illustration(prompt: str) -> bytes:
    """Generate one square, low-quality image only after an explicit UI action."""
    response = OpenAI(api_key=os.environ["OPENAI_API_KEY"]).images.generate(
        model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2"),
        prompt=prompt,
        size="1024x1024",
        quality=os.getenv("OPENAI_IMAGE_QUALITY", "low"),
    )
    encoded_image = response.data[0].b64_json
    if not encoded_image:
        raise RuntimeError("The image-generation API returned no image data.")
    return base64.b64decode(encoded_image)
