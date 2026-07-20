import unittest
from unittest.mock import patch

from taxonomy_visuals import resolve_visual_taxonomy, visual_from_taxonomy


class TaxonomyVisualsTests(unittest.TestCase):
    def test_anatidae_resolves_to_waterfowl_renderer(self):
        result = visual_from_taxonomy("Anatidae", "Anseriformes", "Aves")
        self.assertEqual(result["renderer_id"], "bird_waterfowl")
        self.assertEqual(result["archetype"], "Ave acuática")
        self.assertEqual(result["match_level"], "family")

    def test_unknown_taxon_uses_group_fallback(self):
        result = visual_from_taxonomy("Unknownidae", "Unknowniformes", "Aves")
        self.assertEqual(result["renderer_id"], "bird_generic")
        self.assertEqual(result["match_level"], "fallback")

    def test_passerine_family_resolves_to_perching_bird_renderer(self):
        result = visual_from_taxonomy("Tyrannidae", "Passeriformes", "Aves")
        self.assertEqual(result["renderer_id"], "bird_passerine")
        self.assertEqual(result["match_level"], "family")

    @patch("taxonomy_visuals.species.name_backbone")
    def test_gbif_backbone_result_resolves_to_catalog_renderer(self, name_backbone):
        name_backbone.return_value = {
            "classification": [
                {"rank": "CLASS", "name": "Aves"},
                {"rank": "ORDER", "name": "Anseriformes"},
                {"rank": "FAMILY", "name": "Anatidae"},
            ],
        }

        result = resolve_visual_taxonomy("Aythya affinis")

        name_backbone.assert_called_once_with(scientificName="Aythya affinis")
        self.assertEqual(result["renderer_id"], "bird_waterfowl")
        self.assertEqual(result["match_level"], "family")
