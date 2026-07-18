import unittest

from habitat_context import classify_koppen, geometry_length_m, monthly_normals, summarize_osm_elements


class HabitatContextTests(unittest.TestCase):
    def test_summarize_osm_elements_counts_layers_and_road_length(self):
        summary = summarize_osm_elements(
            [
                {
                    "tags": {"building": "yes"},
                    "geometry": [{"lat": 19.0, "lon": -99.0}, {"lat": 19.0, "lon": -99.001}, {"lat": 19.001, "lon": -99.001}],
                },
                {
                    "tags": {"highway": "residential"},
                    "geometry": [{"lat": 19.0, "lon": -99.0}, {"lat": 19.0, "lon": -99.001}],
                },
            ]
        )
        self.assertEqual(summary["mapped_buildings"], 1)
        self.assertEqual(summary["mapped_roads"], 1)
        self.assertGreater(summary["mapped_road_length_km"], 0)
        self.assertEqual(summary["building_features"][0]["geometry"]["type"], "Polygon")

    def test_geometry_length_uses_geographic_distance(self):
        length = geometry_length_m([{"lat": 0.0, "lon": 0.0}, {"lat": 0.0, "lon": 0.01}])
        self.assertGreater(length, 1_000)
        self.assertLess(length, 1_200)

    def test_koppen_tropical_rainforest_maps_to_potential_forest(self):
        climate = classify_koppen([26.0] * 12, [120.0] * 12, 19.0)
        self.assertEqual(climate["class"], "Af")
        self.assertIn("Bosque tropical", climate["vegetation"])

    def test_monthly_normals_aggregate_daily_values(self):
        temperatures, precipitation = monthly_normals(
            ["2020-01-01", "2020-01-02", "2021-01-01", "2021-01-02"] + [f"2020-{month:02d}-01" for month in range(2, 13)],
            [20.0, 22.0, 24.0, 26.0] + [20.0] * 11,
            [1.0, 3.0, 2.0, 4.0] + [5.0] * 11,
        )
        self.assertEqual(len(temperatures), 12)
        self.assertAlmostEqual(temperatures[0], 23.0)
        self.assertAlmostEqual(precipitation[0], 5.0)
