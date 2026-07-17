import unittest

from export import observations_to_csv
from schema import FieldObservation


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


if __name__ == "__main__":
    unittest.main()
