"""Local, credited demo evidence packaged with the application."""

from __future__ import annotations

import csv
import mimetypes
from dataclasses import dataclass
from pathlib import Path


DEMO_DIRECTORY = Path(__file__).parent / "samples" / "samples_for_demo"
DEMO_CATALOG = DEMO_DIRECTORY / "samples_directory.csv"


@dataclass(frozen=True)
class DemoSample:
    """A catalog entry whose evidence remains local to the deployed app."""

    path: Path
    sample_type: str
    citation: str
    latitude: float
    longitude: float

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def mime_type(self) -> str:
        if self.sample_type == "audio_bird":
            return "audio/mpeg"
        if self.sample_type == "audio_record":
            return "audio/mp4"
        guessed, _ = mimetypes.guess_type(self.name)
        return guessed or "application/octet-stream"

    @property
    def type(self) -> str:
        """Mirror Streamlit's UploadedFile media-type attribute."""
        return self.mime_type

    def getvalue(self) -> bytes:
        """Match the small subset of Streamlit UploadedFile used by services."""
        return self.path.read_bytes()


def load_demo_samples(catalog_path: Path = DEMO_CATALOG) -> list[DemoSample]:
    """Load only valid local catalog records; never trust paths outside the demo folder."""
    samples: list[DemoSample] = []
    root = DEMO_DIRECTORY.resolve()
    with catalog_path.open(encoding="utf-8-sig", newline="") as catalog_file:
        for row in csv.DictReader(catalog_file):
            raw_path = (row.get("file") or "").replace("\\", "/")
            candidate = (Path(__file__).parent / raw_path).resolve()
            if root not in candidate.parents or not candidate.is_file():
                continue
            try:
                latitude, longitude = float(row["lat"]), float(row["long"])
            except (KeyError, TypeError, ValueError):
                continue
            samples.append(
                DemoSample(
                    path=candidate,
                    sample_type=(row.get("type") or "").strip(),
                    citation=(row.get("citation") or "").strip(),
                    latitude=latitude,
                    longitude=longitude,
                )
            )
    return samples


def sample_by_name(samples: list[DemoSample], name: str | None) -> DemoSample | None:
    """Retrieve a selected demo by its file name, not an arbitrary browser value."""
    return next((sample for sample in samples if sample.name == name), None)
