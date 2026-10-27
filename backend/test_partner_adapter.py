import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

from backend.app.partner_adapter import PartnerInvalidInput, PartnerModelAdapter, PartnerModelUnavailable


class PartnerAdapterTests(unittest.TestCase):
    def test_release_gate_blocks_unapproved_bundle(self):
        adapter = PartnerModelAdapter(Path(__file__).parent / "model" / "artifacts" / "teammate_partner_v1")
        with self.assertRaises(PartnerModelUnavailable):
            adapter.verify_release()

    def test_manifest_contains_exact_artifacts(self):
        adapter = PartnerModelAdapter(Path(__file__).parent / "model" / "artifacts" / "teammate_partner_v1")
        manifest = adapter._manifest()
        self.assertFalse(manifest["evaluation_gate_passed"])
        self.assertFalse(manifest["serving_enabled"])
        for filename in adapter.required:
            self.assertTrue((adapter.bundle_dir / filename).is_file(), filename)

    def test_adapter_rejects_partner_contract_metadata_and_bad_images(self):
        adapter = PartnerModelAdapter(Path(__file__).parent / "model" / "artifacts" / "teammate_partner_v1")
        with self.assertRaises(PartnerInvalidInput):
            adapter.predict([b"bad"], ["image-1"], age=50, sex="other", localization="back")
        with self.assertRaises(PartnerInvalidInput):
            adapter.predict([b"bad"], ["image-1"], age=50, sex="unknown", localization="back")

    def test_adapter_exposes_auxiliary_cnn_scores_without_calling_them_final_subtype_output(self):
        adapter = PartnerModelAdapter(Path(__file__).parent / "model" / "artifacts" / "teammate_partner_v1")
        fake = {
            "prediction": "BENIGN",
            "risk_level": "LOW",
            "malignancy_score": 0.12,
            "screening_flag": False,
            "thresholds": {"balanced": 0.5, "screening": 0.18},
            "stream_scores": {"EffNet-B4": 0.1},
            "auxiliary_class_scores": {label: 1 / 7 for label in ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]},
            "auxiliary_class_score_semantics": "auxiliary CNN scores",
            "disclaimer": "Research only.",
        }
        class FakeModel:
            def predict(self, *args, **kwargs):
                return fake
        ok, encoded = cv2.imencode(".jpg", np.zeros((8, 8, 3), dtype=np.uint8))
        self.assertTrue(ok)
        with patch.object(adapter, "_load", return_value=FakeModel()):
            result = adapter.predict([encoded.tobytes()], ["image-1"], age=50, sex="unknown", localization="back", research_mode=True)
        self.assertEqual(result["diagnosisLevel"], "binary")
        self.assertFalse(result["subtypeAvailable"])
        self.assertEqual(result["scoreSource"], "cnn_auxiliary")
        self.assertEqual(len(result["scores"]), 7)
        self.assertFalse(result["scoresAreCalibrated"])


if __name__ == "__main__":
    unittest.main()
