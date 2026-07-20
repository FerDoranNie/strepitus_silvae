import base64
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from habitat_illustration import generate_habitat_illustration, habitat_illustration_prompt


class HabitatIllustrationTests(unittest.TestCase):
    def test_prompt_without_coordinates_does_not_claim_a_location(self):
        prompt = habitat_illustration_prompt("Puma concolor", "Puma")

        self.assertIn("No location is available", prompt)
        self.assertIn("not proof", prompt)
        self.assertIn("Puma concolor", prompt)

    def test_prompt_with_context_uses_environment_as_illustrative_only(self):
        prompt = habitat_illustration_prompt(
            "Puma concolor", "Puma", "Selva Lacandona", "Bosque tropical", "Af"
        )

        self.assertIn("Illustrative environmental context only", prompt)
        self.assertIn("Bosque tropical", prompt)
        self.assertIn("Af", prompt)

    @patch("habitat_illustration.OpenAI")
    def test_generation_decodes_api_image_without_network(self, openai):
        openai.return_value.images.generate.return_value = SimpleNamespace(
            data=[SimpleNamespace(b64_json=base64.b64encode(b"image-bytes").decode())]
        )
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            image = generate_habitat_illustration("test prompt")

        self.assertEqual(image, b"image-bytes")
        openai.return_value.images.generate.assert_called_once()
