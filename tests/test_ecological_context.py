import unittest

from ecological_context import ICONIC_TAXA, aggregate_gbif_records, radius_polygon_wkt, species_row


class EcologicalContextTests(unittest.TestCase):
    def test_species_row_reduces_inaturalist_response(self):
        row = species_row(
            {
                "count": 12,
                "taxon": {
                "name": "Eira barbara",
                "id": 42040,
                    "preferred_common_name": "Tayra",
                    "iconic_taxon_name": "Mammalia",
                },
            }
        )
        self.assertEqual(
            row,
            {
                "Nombre científico": "Eira barbara",
                "Nombre común": "Tayra",
                "Observaciones": 12,
                "Grupo": "Mammalia",
                "Fuente": "iNaturalist",
                "Ficha taxonómica": "https://www.inaturalist.org/taxa/42040",
                "Wikipedia": "https://es.wikipedia.org/w/index.php?search=Eira+barbara",
            },
        )

    def test_supported_groups_include_birds_and_all_taxa(self):
        self.assertIsNone(ICONIC_TAXA["Todos"])
        self.assertEqual(ICONIC_TAXA["Aves"], "Aves")

    def test_gbif_records_are_aggregated_by_species_and_group(self):
        rows = aggregate_gbif_records(
            [
                {"species": "Eira barbara", "vernacularName": "Tayra", "class": "Mammalia"},
                {"species": "Eira barbara", "vernacularName": "Tayra", "class": "Mammalia"},
                {"species": "Ara macao", "class": "Aves"},
            ],
            "Mamíferos",
            15,
        )
        self.assertEqual(rows[0]["Nombre científico"], "Eira barbara")
        self.assertEqual(rows[0]["Observaciones"], 2)
        self.assertEqual(rows[0]["Fuente"], "GBIF")
        self.assertIn("https://www.gbif.org/species/search?q=Eira+barbara", rows[0]["Ficha taxonómica"])
        self.assertIn("Eira+barbara", rows[0]["Wikipedia"])

    def test_radius_polygon_is_closed_wkt(self):
        polygon = radius_polygon_wkt(19.4326, -99.1332, 5, points=4)
        self.assertTrue(polygon.startswith("POLYGON(("))
        self.assertTrue(polygon.endswith("))"))
