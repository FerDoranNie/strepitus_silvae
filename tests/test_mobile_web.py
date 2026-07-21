import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MobileWebTests(unittest.TestCase):
    def test_manifest_has_mobile_metadata_and_icon(self):
        manifest_path = ROOT / "static" / "manifest.webmanifest"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["theme_color"], "#3B6D11")
        self.assertEqual(manifest["icons"][0]["src"], "/app/static/strepitus-silvae-icon.png")

    def test_streamlit_serves_static_mobile_assets(self):
        config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
        app = (ROOT / "app.py").read_text(encoding="utf-8")

        self.assertIn("enableStaticServing = true", config)
        self.assertIn("mobile_web_metadata", app)
        self.assertTrue((ROOT / "components" / "mobile_web_metadata" / "index.html").is_file())
