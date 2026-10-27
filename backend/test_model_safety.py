import unittest
from unittest.mock import patch

from backend.app.model_adapter import V2ModelAdapter


class ModelSafetyTests(unittest.TestCase):
    def test_unavailable_without_verified_artifacts(self):
        status = V2ModelAdapter().status()
        self.assertFalse(status.inference_available)
        self.assertEqual(status.state, "release-disabled")
        self.assertEqual(status.artifact_state, "installed")
        self.assertEqual(status.release_state, "serving-disabled")
        self.assertIn("serving disabled", status.message.lower())

    def test_predict_refuses_to_fabricate(self):
        with self.assertRaises(RuntimeError):
            V2ModelAdapter().predict({})

    def test_research_mode_is_explicit_and_separate_from_release(self):
        with patch.dict("os.environ", {"DERMAVUE_RESEARCH_INFERENCE_ENABLED": "true"}):
            status = V2ModelAdapter().status()
        self.assertTrue(status.research_mode)
        self.assertFalse(status.inference_available)
        self.assertEqual(status.release_state, "serving-disabled")
        self.assertEqual(status.state, "research-enabled-not-loaded")


if __name__ == "__main__":
    unittest.main()
