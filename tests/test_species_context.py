import unittest

from species_context import _claim_value
from three_d_explorer import infer_visual_group


class SpeciesContextTests(unittest.TestCase):
    def test_claim_value_reads_wikidata_item_id(self):
        entity = {"claims": {"P141": [{"mainsnak": {"datavalue": {"value": {"id": "Q211005"}}}}]}}
        self.assertEqual(_claim_value(entity, "P141"), "Q211005")

    def test_visual_group_falls_back_to_stylized_mammal(self):
        self.assertEqual(infer_visual_group("Urocyon cinereoargenteus", "Zorro gris"), "mamífero")

    def test_visual_group_detects_bird_terms(self):
        self.assertEqual(infer_visual_group("Dives dives", "Melodious Blackbird"), "ave")

    def test_visual_group_detects_spanish_duck_name(self):
        self.assertEqual(infer_visual_group("Aythya affinis", "Pato boludo menor"), "ave")
