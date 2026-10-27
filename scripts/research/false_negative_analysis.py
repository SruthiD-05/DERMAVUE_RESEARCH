"""Post-hoc analysis of frozen binary melanoma false negatives."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


QUALITY_COLUMNS = [
    "width", "height", "laplacian_variance", "mean_intensity",
    "intensity_std", "mean_saturation", "clipped_fraction",
]


def _svg_header(width: int = 760, height: int = 430) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="white"/><style>text{{font-family:Arial,sans-serif;font-size:13px}} .axis{{stroke:#333;stroke-width:1}} .grid{{stroke:#ddd;stroke-width:1}} .blue{{fill:#4472c4;stroke:#2f5597}} .orange{{fill:#ed7d31;stroke:#c55a11}} .lineblue{{fill:none;stroke:#4472c4;stroke-width:3}} .lineorange{{fill:none;stroke:#ed7d31;stroke-width:3}}</style>'


def _svg_text(x: float, y: float, value: str, anchor: str = "start") -> str:
    escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">{escaped}</text>'


def _write_probability_svg(path: Path, false_negatives: pd.Series, true_positives: pd.Series) -> None:
    width, height = 760, 430
    left, top, plot_width, plot_height = 70, 35, 650, 320
    bins = np.linspace(0, 1, 16)
    fn_counts, _ = np.histogram(false_negatives, bins=bins)
    tp_counts, _ = np.histogram(true_positives, bins=bins)
    maximum = max(1, int(max(fn_counts.max(initial=0), tp_counts.max(initial=0))))
    svg = [_svg_header(width, height)]
    for tick in range(0, maximum + 1, max(1, maximum // 5)):
        y = top + plot_height - tick / maximum * plot_height
        svg.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}"/>')
        svg.append(_svg_text(left - 8, y + 4, str(tick), "end"))
    bar_width = plot_width / 15
    for index, count in enumerate(fn_counts):
        x = left + index * bar_width + 2
        bar_height = count / maximum * plot_height
        svg.append(f'<rect class="blue" opacity="0.65" x="{x:.1f}" y="{top + plot_height - bar_height:.1f}" width="{bar_width - 4:.1f}" height="{bar_height:.1f}"/>')
    for index, count in enumerate(tp_counts):
        x = left + index * bar_width + bar_width * 0.28
        bar_height = count / maximum * plot_height
        svg.append(f'<rect class="orange" opacity="0.65" x="{x:.1f}" y="{top + plot_height - bar_height:.1f}" width="{bar_width * 0.45:.1f}" height="{bar_height:.1f}"/>')
    svg.extend([f'<line class="axis" x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}"/>', _svg_text(left + plot_width / 2, 405, "Predicted melanoma probability", "middle"), _svg_text(18, top + plot_height / 2, "Images", "middle"), _svg_text(155, 20, "False negatives", "start"), '<rect class="blue" x="135" y="10" width="14" height="14"/>', _svg_text(355, 20, "Melanoma true positives", "start"), '<rect class="orange" x="335" y="10" width="14" height="14"/>', '</svg>'])
    path.write_text("".join(svg), encoding="utf-8")


def _write_quality_svg(path: Path, false_negatives: pd.Series, true_positives: pd.Series) -> None:
    values = [false_negatives.dropna().to_numpy(), true_positives.dropna().to_numpy()]
    maximum = max(1.0, max(float(array.max(initial=0.0)) for array in values))
    width, height = 760, 430
    left, top, plot_width, plot_height = 90, 35, 600, 320
    svg = [_svg_header(width, height)]
    for tick in range(0, 6):
        value = maximum * tick / 5
        y = top + plot_height - tick / 5 * plot_height
        svg.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}"/>')
        svg.append(_svg_text(left - 8, y + 4, f"{value:.0f}", "end"))
    for index, array in enumerate(values):
        if len(array) == 0:
            continue
        q1, median, q3 = np.quantile(array, [0.25, 0.5, 0.75])
        low, high = float(array.min()), float(array.max())
        x = left + plot_width * (0.28 + index * 0.44)
        scale = lambda value: top + plot_height - float(value) / maximum * plot_height
        color = "blue" if index == 0 else "orange"
        svg.extend([f'<line class="axis" x1="{x:.1f}" y1="{scale(low):.1f}" x2="{x:.1f}" y2="{scale(high):.1f}"/>', f'<rect class="{color}" x="{x - 36:.1f}" y="{scale(q3):.1f}" width="72" height="{scale(q1) - scale(q3):.1f}"/>', f'<line class="axis" x1="{x - 36:.1f}" y1="{scale(median):.1f}" x2="{x + 36:.1f}" y2="{scale(median):.1f}"/>', _svg_text(x, 390, "False negatives" if index == 0 else "Melanoma true positives", "middle")])
    svg.extend([_svg_text(left + plot_width / 2, 415, "Laplacian variance (focus proxy)", "middle"), '</svg>'])
    path.write_text("".join(svg), encoding="utf-8")


def _write_coverage_svg(path: Path, coverage: pd.DataFrame) -> None:
    width, height = 760, 430
    left, top, plot_width, plot_height = 70, 35, 650, 320
    svg = [_svg_header(width, height)]
    for tick in range(0, 6):
        y = top + plot_height - tick / 5 * plot_height
        svg.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}"/>')
        svg.append(_svg_text(left - 8, y + 4, f"{tick / 5:.1f}", "end"))
    def points(series):
        return " ".join(f'{left + float(x) * plot_width:.1f},{top + plot_height - float(y) * plot_height:.1f}' for x, y in zip(coverage["requested_coverage"], series))
    svg.append(f'<polyline class="lineblue" points="{points(coverage["melanoma_retention_rate"])}"/>')
    retained_fn_fraction = 1.0 - coverage["false_negatives_retained"] / max(1, int(coverage["false_negatives_retained"].max()))
    svg.append(f'<polyline class="lineorange" points="{points(retained_fn_fraction)}"/>')
    svg.extend([_svg_text(left + plot_width / 2, 405, "Confidence coverage", "middle"), _svg_text(155, 20, "Melanoma retention", "start"), _svg_text(405, 20, "1 - retained FN fraction", "start"), '</svg>'])
    path.write_text("".join(svg), encoding="utf-8")


def _bootstrap_fn_rate(frame: pd.DataFrame, seed: int = 42, repeats: int = 1000) -> list[float]:
    group_column = "lesion_id" if "lesion_id" in frame.columns else None
    rng = np.random.default_rng(seed)
    values = []
    if group_column:
        group_codes, groups = pd.factorize(frame[group_column], sort=False)
        labels = frame["binary_label"].to_numpy()
        fn = frame["false_negative"].to_numpy()
        grouped = np.column_stack([
            np.bincount(group_codes, weights=(labels == 1).astype(float)),
            np.bincount(group_codes, weights=fn.astype(float)),
        ])
        for _ in range(repeats):
            sampled = rng.choice(len(groups), size=len(groups), replace=True)
            denominator, numerator = grouped[sampled].sum(axis=0)
            values.append(float(numerator / denominator) if denominator else 0.0)
    else:
        labels = frame["binary_label"].to_numpy()
        fn = frame["false_negative"].to_numpy()
        for _ in range(repeats):
            sampled = rng.integers(0, len(frame), size=len(frame))
            denominator = (labels[sampled] == 1).sum()
            numerator = fn[sampled].sum()
            values.append(float(numerator / denominator) if denominator else 0.0)
    return [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]


def _coverage_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_melanoma = int((frame["binary_label"] == 1).sum())
    for requested in np.linspace(0.1, 1.0, 10):
        count = max(1, int(round(len(frame) * requested)))
        retained = frame.sort_values("confidence", ascending=False).head(count)
        retained_melanoma = retained["binary_label"] == 1
        rows.append({
            "requested_coverage": float(requested),
            "retained_samples": int(len(retained)),
            "retained_melanoma": int(retained_melanoma.sum()),
            "excluded_melanoma": int(total_melanoma - retained_melanoma.sum()),
            "false_negatives_retained": int(retained["false_negative"].sum()),
            "melanoma_retention_rate": float(retained_melanoma.sum() / total_melanoma) if total_melanoma else None,
        })
    return pd.DataFrame(rows)


def analyze(manifest_path: Path, predictions_path: Path, quality_path: Path, out_dir: Path) -> dict:
    manifest = pd.read_csv(manifest_path)
    predictions = pd.read_csv(predictions_path)
    repeated = (set(manifest.columns) & set(predictions.columns)) - {"image_id"}
    predictions = predictions.drop(columns=sorted(repeated), errors="ignore")
    frame = manifest.merge(predictions, on="image_id", how="inner", validate="one_to_one")
    if len(frame) != len(manifest):
        raise ValueError("Predictions do not cover the complete binary test manifest.")
    if quality_path.exists():
        quality = pd.read_csv(quality_path)
        quality = quality[["image_id", *[column for column in QUALITY_COLUMNS if column in quality.columns]]].drop_duplicates("image_id")
        frame = frame.merge(quality, on="image_id", how="left", validate="one_to_one")
    frame["binary_label"] = frame["binary_label"].astype(int)
    frame["predicted_label"] = frame["predicted_label"].astype(int)
    frame["probability_melanoma"] = frame["probability_melanoma"].astype(float)
    frame["confidence"] = np.maximum(frame["probability_melanoma"], 1.0 - frame["probability_melanoma"])
    frame["false_negative"] = ((frame["binary_label"] == 1) & (frame["predicted_label"] == 0)).astype(int)
    frame["false_positive"] = ((frame["binary_label"] == 0) & (frame["predicted_label"] == 1)).astype(int)
    false_negatives = frame[frame["false_negative"] == 1].copy().sort_values("probability_melanoma")
    true_melanoma_positives = frame[(frame["binary_label"] == 1) & (frame["predicted_label"] == 1)]
    false_negatives.to_csv(out_dir / "false_negatives.csv", index=False)

    summary = {
        "data_provenance": "genuine",
        "manifest": str(manifest_path.resolve()),
        "predictions": str(predictions_path.resolve()),
        "post_hoc_only": True,
        "used_for_model_selection": False,
        "test_samples": int(len(frame)),
        "melanoma_test_rows": int((frame["binary_label"] == 1).sum()),
        "false_negatives": int(len(false_negatives)),
        "false_negative_rate_among_melanoma": float(false_negatives.shape[0] / max(1, (frame["binary_label"] == 1).sum())),
        "false_negative_rate_grouped_bootstrap_95ci": _bootstrap_fn_rate(frame),
        "false_negative_probability": {
            "mean": float(false_negatives["probability_melanoma"].mean()),
            "median": float(false_negatives["probability_melanoma"].median()),
            "min": float(false_negatives["probability_melanoma"].min()),
            "max": float(false_negatives["probability_melanoma"].max()),
        },
        "true_melanoma_positive_probability": {
            "mean": float(true_melanoma_positives["probability_melanoma"].mean()),
            "median": float(true_melanoma_positives["probability_melanoma"].median()),
        },
        "false_negative_original_dx": false_negatives["dx"].value_counts().to_dict() if "dx" in false_negatives else {},
        "false_negative_localization": false_negatives["localization"].value_counts().to_dict() if "localization" in false_negatives else {},
        "false_negative_sex": false_negatives["sex"].value_counts().to_dict() if "sex" in false_negatives else {},
        "source_metadata_available": [column for column in ("dataset", "localization", "sex", "age") if column in frame.columns],
    }
    if "age" in false_negatives:
        summary["false_negative_age"] = {
            "count_non_missing": int(false_negatives["age"].notna().sum()),
            "mean": float(false_negatives["age"].mean()),
            "median": float(false_negatives["age"].median()),
        }
    for column in QUALITY_COLUMNS:
        if column in false_negatives and false_negatives[column].notna().any():
            summary.setdefault("quality_comparison", {})[column] = {
                "false_negative_mean": float(false_negatives[column].mean()),
                "melanoma_true_positive_mean": float(true_melanoma_positives[column].mean()),
            }

    coverage = _coverage_table(frame)
    coverage.to_csv(out_dir / "confidence_coverage_melanoma.csv", index=False)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    _write_probability_svg(
        out_dir / "false_negative_probability.svg",
        false_negatives["probability_melanoma"],
        true_melanoma_positives["probability_melanoma"],
    )

    if "laplacian_variance" in frame:
        _write_quality_svg(
            out_dir / "false_negative_quality.svg",
            false_negatives["laplacian_variance"],
            true_melanoma_positives["laplacian_variance"],
        )

    _write_coverage_svg(out_dir / "confidence_coverage_melanoma.svg", coverage)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--quality-metrics", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    try:
        print(json.dumps(analyze(args.manifest, args.predictions, args.quality_metrics, args.out_dir), indent=2, default=str))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"FALSE-NEGATIVE ANALYSIS BLOCKED: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
