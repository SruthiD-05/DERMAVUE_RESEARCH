import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "v2" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


prep = load("prepare_real_dataset", "prepare_real_dataset.py")
evaluation = load("evaluate_real_predictions", "evaluate_real_predictions.py")
binary_prep = load("prepare_binary_dataset", "prepare_binary_dataset.py")


class PipelineTests(unittest.TestCase):
    def test_missing_metadata_columns_are_rejected(self):
        frame = pd.DataFrame({"image_id": ["a"]})
        missing = prep.REQUIRED - set(frame.columns)
        self.assertIn("lesion_id", missing)

    def test_group_split_has_no_group_overlap(self):
        patients = [f"p{class_id}_{rep}" for class_id in range(5) for rep in range(5)]
        frame = pd.DataFrame({
            "patient_id": [item for item in patients for _ in range(2)],
            "lesion_id": [f"l{i}" for i in range(len(patients)) for _ in range(2)],
            "risk_label": [class_id for class_id in range(5) for _ in range(10)],
        })
        split = prep._split_groups(frame, "patient_id", 42, 0.2, 0.25)
        self.assertEqual(set(split), {"train", "validation", "test"})
        for left in ("train", "validation", "test"):
            for right in ("train", "validation", "test"):
                if left < right:
                    self.assertFalse(set(frame.loc[split == left, "patient_id"]) & set(frame.loc[split == right, "patient_id"]))

    def test_evaluation_reports_target_without_claiming_it(self):
        manifest = pd.DataFrame({"image_id": ["a", "b", "c", "d", "e"], "risk_label": [0, 1, 2, 3, 4], "split": ["test"] * 5})
        predictions = pd.DataFrame({"image_id": ["a", "b", "c", "d", "e"], "predicted_label": [0, 1, 2, 3, 0]})
        result = evaluation.evaluate(manifest, predictions)
        self.assertEqual(result["test_samples"], 5)
        self.assertFalse(result["target_reached"])
        self.assertIn("confusion_matrix", result)

    def test_probability_metrics_keep_labels_aligned_when_predictions_are_shuffled(self):
        manifest = pd.DataFrame({
            "image_id": ["a", "b", "c", "d", "e"],
            "risk_label": [0, 1, 2, 3, 4],
            "split": ["test"] * 5,
        })
        predictions = pd.DataFrame({
            "image_id": ["e", "c", "a", "d", "b"],
            "predicted_label": [4, 2, 0, 3, 1],
            "probability_0": [0, 0, 1, 0, 0],
            "probability_1": [0, 0, 0, 0, 1],
            "probability_2": [0, 1, 0, 0, 0],
            "probability_3": [0, 0, 0, 1, 0],
            "probability_4": [1, 0, 0, 0, 0],
        })
        result = evaluation.evaluate(manifest, predictions)
        self.assertAlmostEqual(result["macro_auroc"], 1.0)

    def test_binary_contract_preserves_other_dx_limitation(self):
        self.assertEqual(binary_prep.TASK, "binary_melanoma_other_dx_v1")
        self.assertEqual(binary_prep.LABELS[1], "Melanoma")
        self.assertIn("bcc", binary_prep.KNOWN_DX - {"mel"})

    def test_binary_evaluation_reports_calculation_target_separately(self):
        manifest = pd.DataFrame({
            "image_id": ["a", "b", "c", "d"],
            "binary_label": [0, 0, 1, 1],
            "split": ["test"] * 4,
        })
        predictions = pd.DataFrame({
            "image_id": ["d", "b", "a", "c"],
            "predicted_label": [1, 0, 0, 1],
            "probability_0": [0.1, 0.8, 0.9, 0.2],
            "probability_1": [0.9, 0.2, 0.1, 0.8],
        })
        result = evaluation.evaluate(manifest, predictions, task="binary_melanoma_other_dx_v1")
        self.assertEqual(result["task"], "binary_melanoma_other_dx_v1")
        self.assertIn("auroc", result)
        self.assertEqual(result["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
