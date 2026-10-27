import unittest

import numpy as np
import pandas as pd

from false_negative_analysis import _coverage_table
from threshold_operating_point import THRESHOLDS, _metrics


class ResearchAnalysisTests(unittest.TestCase):
    def test_threshold_grid_is_fixed_and_metrics_report_false_negatives(self):
        self.assertEqual(THRESHOLDS[0], 0.1)
        self.assertEqual(THRESHOLDS[-1], 0.9)
        result = _metrics(np.array([0, 0, 1, 1]), np.array([0.1, 0.6, 0.4, 0.9]), 0.5)
        self.assertEqual(result["false_negatives"], 1)
        self.assertAlmostEqual(result["melanoma_sensitivity"], 0.5)

    def test_confidence_coverage_reports_melanoma_retention(self):
        frame = pd.DataFrame({
            "binary_label": [0, 0, 1, 1],
            "predicted_label": [0, 1, 0, 1],
            "confidence": [0.99, 0.95, 0.60, 0.55],
            "false_negative": [0, 0, 1, 0],
        })
        result = _coverage_table(frame)
        self.assertEqual(len(result), 10)
        self.assertIn("melanoma_retention_rate", result.columns)


if __name__ == "__main__":
    unittest.main()
