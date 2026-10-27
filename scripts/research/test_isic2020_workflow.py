import hashlib
import json
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manual_overlap_review import DISPOSITIONS, SCHEMA_VERSION
from prepare_isic2020_development import LABELS


ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "data" / "reports" / "isic2020_ham10000_overlap_review_v1.json"
REVIEW_REPORT = ROOT / "data" / "reports" / "isic2020_ham10000_overlap_review_v1_report.json"
READINESS = ROOT / "data" / "manifests" / "isic2020_melanoma_vs_nonmelanoma_v1_development" / "task_readiness.json"
EXTERNAL = ROOT / "data" / "manifests" / "isic2020_binary_melanoma_v1_external_eval" / "external_evaluation.csv"
CONFIG = ROOT / "experiments" / "isic2020_melanoma_vs_nonmelanoma_v1" / "config.json"
FAST_CONFIG = ROOT / "experiments" / "isic2020_melanoma_vs_nonmelanoma_v1" / "config_cpu128_seed42.json"
HAM_READINESS = ROOT / "data" / "manifests" / "isic2020_melanoma_vs_nonmelanoma_v1_ham_development" / "development_validation.json"


class ISIC2020WorkflowTests(unittest.TestCase):
    def test_review_file_is_source_anchored_and_unreviewed(self):
        payload = json.loads(REVIEW.read_text(encoding="utf-8"))
        audit = ROOT / "data" / "reports" / "isic2020_ham10000_overlap_dct.json"
        digest = hashlib.sha256(audit.read_bytes()).hexdigest()
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        self.assertEqual(payload["source_audit_sha256"], digest)
        self.assertEqual(len(payload["candidates"]), 1187)
        self.assertEqual({item["disposition"] for item in payload["candidates"]}, {"unreviewed"})
        self.assertTrue(all(set(item) >= {"left", "right", "hamming_distance", "reviewer", "rationale"} for item in payload["candidates"]))

    def test_review_report_does_not_invent_dispositions(self):
        report = json.loads(REVIEW_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["report_status"], "review_incomplete")
        self.assertEqual(report["exact_cross_dataset_match_count"], 0)
        self.assertEqual(report["disposition_counts"], {
            "confirmed_duplicate": 0,
            "not_duplicate": 0,
            "uncertain": 0,
            "unreviewed": 1187,
        })
        self.assertEqual(set(report["disposition_counts"]), DISPOSITIONS)

    def test_isic_label_contract_and_external_provenance(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        frame = pd.read_csv(EXTERNAL)
        self.assertEqual(config["label_mapping"], LABELS)
        self.assertEqual(set(frame["data_provenance"]), {"genuine_external"})
        self.assertEqual(set(frame["split"]), {"external_evaluation"})
        self.assertNotIn("synthetic", " ".join(frame.astype(str).fillna("").to_numpy().ravel()).lower())

    def test_development_readiness_is_blocked_without_using_external_rows(self):
        report = json.loads(READINESS.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "blocked_no_eligible_development_rows")
        self.assertEqual(report["eligible_development_rows"], 0)
        self.assertEqual(report["train_rows"], 0)
        self.assertEqual(report["validation_rows"], 0)
        self.assertFalse(report["external_manifest_used_for_development"])
        self.assertEqual(report["frozen_external_rows_excluded"], 5988)
        self.assertEqual(report["source_labeled_rows"], 6002)

    def test_ham_development_manifest_is_genuine_and_preserves_test(self):
        report = json.loads(HAM_READINESS.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["train_rows"], 6641)
        self.assertEqual(report["validation_rows"], 1153)
        self.assertEqual(report["excluded_overlap_rows"], 222)
        self.assertFalse(report["patient_id_available"])
        self.assertFalse(report["preserved_ham_test_used_for_training"])
        self.assertFalse(report["isic_external_used_for_training"])
        self.assertFalse(report["old_ham_binary_checkpoint_reused"])

    def test_cpu_baseline_keeps_task_contract(self):
        config = json.loads(FAST_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(config["task"], "isic2020_melanoma_vs_nonmelanoma_v1")
        self.assertEqual(config["label_mapping"], LABELS)
        self.assertEqual(config["reproducibility"]["seed"], 42)
        self.assertEqual(config["preprocessing"]["image_size"], 128)


if __name__ == "__main__":
    unittest.main()
