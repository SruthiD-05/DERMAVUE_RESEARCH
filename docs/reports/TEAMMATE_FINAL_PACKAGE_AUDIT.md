# Teammate Final Model Package Audit

Audit date: 2026-10-25  
Project: `F:\\SkinCancer`  
Audit directory: `F:\\SkinCancer\\incoming\\teammate_final_package_audit\\`

## Verdict

**PARTIALLY VERIFIED**

The supplied result files and model package are internally consistent. The
reported confusion matrices, 89.34% image-row accuracy, 91.70% lesion accuracy,
and approximately 0.94/0.95 ROC-AUC recompute from the supplied predictions.
The three CNN checkpoints and XGBoost artifact load successfully and produce
the documented API response.

This does **not** establish independent clinical validation or patient-level
independence. The package contains no train/validation manifests, patient IDs,
duplicate audit, confidence intervals, or evidence that the reported test set
was independent of all training sources. The model has not been integrated into
DermaVue; the existing `503 model_unavailable` gate remains active.

## Supplied archives and hashes

All three archives were found in `C:\\Users\\fahad\\Downloads` and preserved
without modification.

| Archive | Bytes | SHA-256 |
|---|---:|---|
| `skin_cancer_backend.zip` | 7,446 | `773ac9a7b5ce11c3046ae1351f9e1fa39285f9a9a79c269a537b85a01c4d50ca` |
| `results_for_fahad.zip` | 386,877 | `a09f8dd5a854dd75fb84aa83f241561882abf29f64ddc66268d7d63318273b19` |
| `backend_model.zip` | 628,054,846 | `abe4e156f788da75ac7b1d11a8151a20e4d6fd92564b4cc11fb219e144b4ae29` |

Extraction was isolated into separate `backend`, `results`, and `model`
subdirectories. Existing project backend, frontend, checkpoints, HAM10000,
and ISIC artifacts were not overwritten.

## Archive contents

### Backend archive

Contains `app.py`, `inference.py`, `requirements.txt`, README documentation,
and a model placeholder. It does not contain weights.

### Results archive

- `test_predictions.csv`: 1,510 rows.
- `test_predictions_per_lesion.csv`: 1,121 rows.
- `evaluation_summary.json`.
- `confusion_matrices_image_and_lesion.png`.

Extracted result hashes:

| File | SHA-256 |
|---|---|
| `test_predictions.csv` | `9ecc6108fa9b0a1c0eafa88231f107ba909130fe32ec0b6e8691a6a6cffb19b9` |
| `test_predictions_per_lesion.csv` | `eb58882b7347c16ddb1c276e72364687365f6500d725d46dd594601144b28939` |
| `evaluation_summary.json` | `b2a92f0a79a0495e48cfe094a33e69201e20656bd1ae91bdbac6794bb8d58ed4` |
| `confusion_matrices_image_and_lesion.png` | `82bf5c2b7d18a84ad8322b33b1850c1c9e51a7d93b9c0944bc82fbe9865d875c` |

### Model archive

| File | Bytes | SHA-256 |
|---|---:|---|
| `config.json` | 1,028 | `d5ab91d6cac02264a126f318d58d0696972abcdc1ece281fc8647ed7a3e77936` |
| `EffNet-B4.keras` | 218,600,050 | `4f748c53920fc394b5682442208c4b60116796cf14f4c3e563052d2d6686aa3a` |
| `EffNet-B4-s7.keras` | 218,600,050 | `28eac3a491a344b62cfb4eaab24e2d874df4fe34f6ff124fec3e6acf4c95cc358` |
| `EffNetV2-S.keras` | 248,847,017 | `6ed23c6125a35ac171908f91ba479efb7f3e44bcf87de2f5ac336fddaef79f0c` |
| `xgb_tabular.json` | 779,730 | `88ef813e4bc81b36856a53cd6a64aeb4fcc576660d499290136575abc55c1116` |

## Model contract

The verified configuration specifies:

- 384×384 image inputs.
- Seven classes: `akiec`, `bcc`, `bkl`, `df`, `mel`, `nv`, `vasc`.
- Malignant positive class: `akiec`, `bcc`, and `mel`.
- Three CNN streams: EfficientNet-B4, EfficientNetV2-S, and a second
  EfficientNet-B4 seed-7 checkpoint.
- Eight TTA views in the documented configuration.
- DullRazor-style inpainting, ITA skin-tone proxy, Shades-of-Gray correction,
  and resize preprocessing.
- Nine ABCD/texture features plus age, sex, UV-site, and localization features
  for XGBoost.
- Logistic fusion of four stream logits.
- Balanced threshold `0.5`; screening threshold `0.18`.
- Multiple images are assumed to belong to one lesion; fused image scores are
  averaged for the lesion-level score.

The archive filenames match the loading logic in `inference.py` exactly.

## Independent metric recomputation

The image CSV schema contains image ID, lesion ID, diagnosis, binary label,
image-level score, lesion-average score, prediction, three CNN scores, and the
ABCD/metadata score. The lesion CSV contains one row per lesion, its label,
image count, lesion score, and prediction.

The supplied confusion matrices recompute exactly:

| Unit | TN | FP | FN | TP | Accuracy | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Image rows using supplied `y_pred` | 1,170 | 53 | 108 | 179 | 89.3377% | 0.9376 using lesion-average score |
| Lesions | 916 | 30 | 63 | 112 | 91.7038% | 0.9522 |

Additional recomputed metrics at threshold 0.5:

| Unit | Sensitivity | Specificity | Precision | F1 |
|---|---:|---:|---:|---:|
| Image rows using supplied prediction | 62.3693% | 95.6664% | 77.1552% | 0.6898 |
| Lesions | 64.0000% | 96.8288% | 78.8732% | 0.7066 |

The image set contains 1,223 negative and 287 positive rows. The lesion set
contains 946 negative and 175 positive lesions. Majority-class baselines are
80.9934% and 84.3889%, respectively.

### Important interpretation of the image metric

The reported image confusion matrix is reproduced by thresholding
`fused_score_lesion_avg`, not by thresholding the raw `fused_score_image`
column. The raw image score produces a different result:

`[[1173, 50], [105, 182]]`, 89.7351% accuracy, and ROC-AUC 0.9334.

Therefore, “per-image” means image-row accounting after the lesion-average
score has been broadcast to every image of that lesion. It is not an entirely
independent raw per-image prediction metric. The reported 89.34% versus 91.70%
discrepancy is consequently explained by lesion aggregation and different
denominators: 1,510 image rows versus 1,121 lesions.

The two CSVs agree on lesion IDs, labels, image counts, scores, and predictions
to the supplied six-decimal precision.

## Split and leakage limitations

The `evaluation_summary.json` claims a lesion-level 75/10/15 split with seed
42, 996 validation images, and 1,510 test images. The code in the supplied
notebook also uses lesion-level stratification and asserts no lesion crosses
its three splits.

However, the final package does not include the train/validation manifests,
full lesion lists, patient identifiers, duplicate audit, or source-image
checksums. Therefore:

- The claimed split cannot be independently reconstructed from the package
  alone.
- Patient-level independence cannot be established. The procedure groups by
  lesion, not patient, and HAM10000 patient identifiers are not supplied in
  this package.
- Training reportedly includes non-HAM ISIC 2019 images, but no ISIC 2019
  files, source manifest, deduplication report, or hashes are supplied here.
- Test-set threshold tuning cannot be shown to have occurred because the
  validation predictions and selection logs are absent, although the supplied
  code documents validation-only threshold selection.
- No confidence intervals or uncertainty estimates are supplied.

The claims are reproducible from the packaged predictions, but the broader
generalization and independence claims remain unverified.

## Checkpoint loading and API smoke test

An isolated virtual environment was created at:
`F:\\SkinCancer\\incoming\\teammate_final_package_audit\\venv\\`.

The available environment used TensorFlow 2.21.0, XGBoost 3.4.1, OpenCV 5.0.0,
and FastAPI 0.135.3. The supplied requirements pin TensorFlow to 2.20.0 but do
not pin most other dependencies. `python-multipart` was installed into the
isolated environment because it was declared but absent.

Actual smoke-test results:

- All three CNN checkpoints loaded successfully.
- XGBoost loaded successfully.
- One-image and duplicate two-image inference succeeded.
- Duplicate two-image input produced the same lesion score, confirming the
  documented averaging behavior for identical inputs.
- `/info`: HTTP 200.
- Valid `/predict`: HTTP 200 with the documented response fields.
- Invalid image bytes: HTTP 400.
- Unknown localization: HTTP 400.
- Missing multipart files: HTTP 422.
- Smoke inference used `TTA_VIEWS=2` to reduce CPU cost; the packaged config
  specifies eight views, so this was a software smoke test rather than a
  reproduction of the final benchmark inference setting.

The permitted image was the existing public HAM10000 image
`ISIC_0024306.jpg`; no private patient photographs were used.

## Integration blockers

Do not integrate this package into DermaVue yet.

1. The partner API uses `POST /predict` with a `files` field, while DermaVue
   expects `POST /api/cases/{case_id}/analyze` with `images` and `image_ids`.
2. The partner response schema (`prediction`, `malignancy_score`, and risk
   fields) differs from the existing DermaVue `AnalysisResult` contract.
3. The model package has no release manifest, evaluation checksum manifest,
   patient-level independence evidence, duplicate audit, or confidence
   intervals.
4. The runtime was smoke-tested with TensorFlow 2.21.0 rather than the
   declared 2.20.0 requirement.
5. The supplied backend has previously identified security concerns including
   open CORS, no upload-size/count limits, weak metadata validation, and
   unpinned dependencies.
6. The reported metrics are research results on HAM10000-derived data, not
   clinical validation or authorization for patient analysis.

The next integration step is to create a separately reviewed adapter and
release manifest only after dependency pinning, full split/provenance review,
and API contract mapping are approved. Until then, the existing DermaVue
analysis endpoint must continue returning `503 model_unavailable`.
