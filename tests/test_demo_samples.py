import unittest

from demo_samples import load_demo_samples, sample_by_name


class DemoSamplesTests(unittest.TestCase):
    def test_catalog_loads_existing_credited_samples(self):
        samples = load_demo_samples()

        self.assertEqual(len(samples), 6)
        self.assertTrue(all(sample.path.is_file() for sample in samples))
        self.assertTrue(all(sample.citation for sample in samples))

    def test_bird_audio_sample_has_uploaded_file_compatibility(self):
        samples = load_demo_samples()
        sample = next(sample for sample in samples if sample.sample_type == "audio_bird")

        self.assertEqual(sample.mime_type, "audio/mpeg")
        self.assertEqual(sample.type, "audio/mpeg")
        self.assertGreater(len(sample.getvalue()), 0)
        self.assertIs(sample_by_name(samples, sample.name), sample)
