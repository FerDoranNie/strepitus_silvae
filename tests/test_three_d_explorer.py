import unittest

from three_d_explorer import visual_group_for_renderer


class ThreeDExplorerTests(unittest.TestCase):
    def test_waterfowl_renderer_uses_specific_visual_label(self):
        self.assertEqual(
            visual_group_for_renderer("bird_waterfowl", "Aythya affinis", "Lesser scaup"),
            "ave acuática",
        )

    def test_other_renderers_keep_generic_taxon_inference(self):
        self.assertEqual(
            visual_group_for_renderer(None, "Dives dives", "Melodious Blackbird"),
            "ave",
        )

    def test_passerine_renderer_never_falls_back_to_a_mammal(self):
        self.assertEqual(
            visual_group_for_renderer("bird_passerine", "Pyrocephalus rubinus", "Mosquero cardenal"),
            "ave paseriforme",
        )
