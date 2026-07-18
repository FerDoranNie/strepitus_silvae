import unittest
import tempfile
from pathlib import Path

from bioacoustics import _name_parts
from export import observations_to_csv
from schema import FieldObservation
from services import _deduplicate_video_records
from video_processor import extract_sampled_frames


class SchemaAndExportTests(unittest.TestCase):
    def setUp(self):
        self.observation = FieldObservation(
            scientificName="Puma concolor", vernacularName="Puma", individualCount=1,
            behavior="desplazándose", organismRemarks="Sin lesiones visibles",
            identificationConfidence="medio", alertaHumanaOVehiculo=False,
            eventDate="2026-07-16", decimalLatitude=19.4, decimalLongitude=-99.1,
            locality="Reserva de prueba", identifiedBy="Strepitus Silvae",
        )

    def test_observation_serializes_date(self):
        self.assertEqual(self.observation.model_dump(mode="json")["eventDate"], "2026-07-16")

    def test_csv_has_darwin_core_columns_and_value(self):
        csv_text = observations_to_csv([self.observation])
        self.assertIn("scientificName", csv_text)
        self.assertIn("Puma concolor", csv_text)

    def test_birdnet_name_parser(self):
        scientific, common = _name_parts("Dives_dives_Melodious_Blackbird")
        self.assertEqual(scientific, "Dives dives")
        self.assertEqual(common, "Melodious Blackbird")

    def test_video_records_merge_repeated_taxa_and_keep_maximum_count(self):
        records = [
            {
                "scientificName": "Urocyon cinereoargenteus", "vernacularName": "Zorro gris",
                "individualCount": 1, "behavior": "caminando", "organismRemarks": "visible",
                "identificationConfidence": "medio", "alertaHumanaOVehiculo": False,
            },
            {
                "scientificName": "urocyon cinereoargenteus", "vernacularName": "Zorro gris",
                "individualCount": 2, "behavior": "caminando", "organismRemarks": "visible",
                "identificationConfidence": "alto", "alertaHumanaOVehiculo": True,
            },
            {
                "scientificName": "Nasua narica", "vernacularName": "Coatí",
                "individualCount": 1, "behavior": "forrajeando", "organismRemarks": "visible",
                "identificationConfidence": "alto", "alertaHumanaOVehiculo": False,
            },
        ]
        merged = _deduplicate_video_records(records)
        self.assertEqual(len(merged), 2)
        fox = next(record for record in merged if record["scientificName"].casefold() == "urocyon cinereoargenteus")
        self.assertEqual(fox["individualCount"], 2)
        self.assertEqual(fox["identificationConfidence"], "alto")
        self.assertTrue(fox["alertaHumanaOVehiculo"])

    def test_video_frame_extraction(self):
        import cv2
        import numpy as np

        with tempfile.TemporaryDirectory() as directory:
            video_path = Path(directory) / "fixture.avi"
            writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"MJPG"), 5, (32, 32))
            for value in (0, 90, 180):
                writer.write(np.full((32, 32, 3), value, dtype=np.uint8))
            writer.release()
            frames = extract_sampled_frames(video_path.read_bytes(), video_path.name, sample_count=3)
        self.assertEqual(len(frames), 3)
        self.assertTrue(all(frame.startswith("data:image/jpeg;base64,") for frame in frames))


if __name__ == "__main__":
    unittest.main()
