import tempfile
import unittest
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_external_predictions import _ece, _point_metrics, _require_completed_overlap_review
from prepare_isic2020_external_manifest import _load_duplicate_ids
from assess_external_compatibility import assess


class ExternalValidationTests(unittest.TestCase):
    def test_incomplete_overlap_review_blocks_external_evaluation(self):
        review = Path(__file__).resolve().parents[2] / "data" / "reports" / "isic2020_ham10000_overlap_review_v1_report.json"
        with self.assertRaises(ValueError):
            _require_completed_overlap_review(review)

    def test_ece_is_zero_for_perfectly_calibrated_two_point_predictions(self):
        self.assertAlmostEqual(_ece(np.array([0, 1]), np.array([0.0, 1.0])), 0.0)

    def test_binary_metrics_include_specificity_and_confusion(self):
        result = _point_metrics(np.array([0, 0, 1, 1]), np.array([0.1, 0.8, 0.2, 0.9]), 0.5)
        self.assertEqual(result["confusion_matrix"], [[1, 1], [1, 1]])
        self.assertEqual(result["false_negatives"], 1)
        self.assertAlmostEqual(result["specificity"], 0.5)
        self.assertAlmostEqual(result["macro_f1"], 0.5)
        self.assertEqual(result["per_class_metrics"]["1"]["support"], 2)

    def test_duplicate_file_loader_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicates.csv"
            pd.DataFrame({"image_name_1": ["a"], "image_name_2": ["b"]}).to_csv(path, index=False)
            ids, pairs = _load_duplicate_ids(path)
        self.assertEqual(ids, {"a", "b"})
        self.assertEqual(pairs, 1)

    def test_ham_other_dx_bundle_is_blocked_for_isic_target_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.csv"
            pd.DataFrame({
                "image_id": ["a"],
                "patient_id": ["p1"],
                "external_binary_label": [1],
                "split": ["external_evaluation"],
                "data_provenance": ["genuine_external"],
                "modality": ["dermoscopic"],
            }).to_csv(manifest, index=False)
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "label_mapping.json").write_text(json.dumps({"0": "Non-melanoma (other HAM10000 dx)", "1": "Melanoma"}), encoding="utf-8")
            (bundle / "training_config.json").write_text(json.dumps({"image": {"size": 128}}), encoding="utf-8")
            (bundle / "feature_names.json").write_text(json.dumps({"metadata_features": ["num__age"]}), encoding="utf-8")
            output = root / "compatibility.json"
            result = assess(manifest, bundle, output)
        self.assertFalse(result["evaluation_allowed"])
        self.assertFalse(result["label_contract_compatible"])



if __name__ == "__main__":
    unittest.main()
