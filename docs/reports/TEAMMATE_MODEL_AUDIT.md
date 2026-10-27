# Teammate Model and Backend Audit

Audit date: 2026-10-24  
Project: `F:\\SkinCancer`  
Scope: `skin_cancer_backend.zip` only. The supplied notebooks were explicitly
excluded from this audit and were not used as evidence.

## Verdict

**UNVERIFIED**

The supplied ZIP contains backend source and a README, but no trained model
weights or reproducible evaluation artifacts. The reported 91.70% per-lesion
accuracy, 89.34% per-image accuracy, and ROC-AUC values cannot be recomputed
from the supplied files. The backend was not integrated and the existing
DermaVue `503 model_unavailable` behavior was preserved.

## Files and provenance

Found in `C:\\Users\\fahad\\Downloads`:

| Item | Status |
|---|---|
| `skin_cancer_backend.zip` | Found and preserved; SHA-256 `773ac9a7b5ce11c3046ae1351f9e1fa39285f9a9a79c269a537b85a01c4d50ca`, 7,446 bytes |
| `backend_model.zip` | **Missing**; no matching file was found in Downloads or the project workspace |
| Supplied notebooks | Present but intentionally ignored per user instruction |

The ZIP was extracted without overwriting project files to:
`F:\\SkinCancer\\incoming\\teammate_backend_audit_20261024\\`.

| Extracted file | Bytes | SHA-256 |
|---|---:|---|
| `backend/app.py` | 2,319 | `245d87a5549f8ac376369cd5546b7f86ead6936a58df8042dc13bfdd854b1821` |
| `backend/inference.py` | 6,775 | `31a69d0221008e159223be3ec96a8b472d3edf3f6e7f86c876c5e5ab2138f84d` |
| `backend/README.md` | 4,029 | `9455a89cdb69fe26bfe51c8b6dd14085541445adbc89354110d1cee95d625f78` |
| `backend/requirements.txt` | 116 | `187d54279d8a489060df902080a37d80d7679747cf7def60266e69e8195cba6f` |
| `backend/model/PUT_MODEL_FILES_HERE.txt` | 84 | `d2270bcea8a0a6aea3dc2680fa9f867337380297934e84a0f5be315cbc359816` |

The model directory contains only the placeholder text file. The expected
`EffNet-B4.keras`, `EffNetV2-S.keras`, `EffNet-B4-s7.keras`,
`xgb_tabular.json`, and `config.json` files are absent.

## Backend implementation audit

The supplied implementation describes a tri-modal ensemble:

- Three Keras CNNs, each producing seven-class softmax probabilities.
- Malignancy is computed as `P(mel) + P(bcc) + P(akiec)` using `MAL_IDX` from
  the missing `config.json`.
- An XGBoost tabular model consumes nine ABCD/texture features plus age, sex,
  UV-site, and localization one-hot values.
- A logistic fusion layer combines logits from the three CNN streams and the
  tabular stream using `STACK_COEF` and `STACK_INTERCEPT` from the missing
  configuration.
- Multiple submitted images are assumed to be photographs of the same lesion;
  fused image-level scores are averaged into one lesion-level score.

The preprocessing code performs resize limiting, DullRazor-style inpainting,
ITA estimation, Shades-of-Gray color correction, and resizing to `IMG` from
the missing configuration. Exact image size, class order, thresholds, sites,
median age, and fusion coefficients cannot be verified without `config.json`.

`malignancy_score` is the mean of the fused sigmoid scores after applying the
stacker to per-image stream logits. `T_ACC` determines `MALIGNANT` versus
`BENIGN`; `T_SCR` determines `screening_flag` and the low/moderate/high risk
category. These values are also unavailable without the model configuration.

Static source inspection found no hardcoded prediction fallback or synthetic
prediction branch. The code loads actual model files if present. However,
startup requires all model files and therefore cannot be tested successfully
in the supplied package.

## API and security findings

The README documents a standalone FastAPI API with `/health`, `/info`, and
`/predict`. This does not match the current DermaVue backend contract:

- Partner API: `POST /predict`, multipart field `files`, optional `age`, `sex`,
  and `localization`.
- DermaVue API: `POST /api/cases/{case_id}/analyze`, multipart fields `images`
  and matching `image_ids`, with a different response schema.

Integration is therefore not compatible without a separately reviewed adapter.

Issues requiring remediation before any deployment include:

- CORS is open to `*` and the README starts Uvicorn on `0.0.0.0`.
- No authentication, authorization, rate limiting, request-size limit, image
  count limit, or decoded-dimension limit is implemented.
- MIME types are not enforced; decoding is attempted based on bytes only.
- `age` is not range- or finite-value validated.
- Any `sex` value other than case-insensitive `male` becomes the same encoded
  value as non-male; documented `female`/`unknown` semantics are not enforced.
- If model startup fails, `/info` dereferences `model.cfg` even when `model`
  is `None`, producing an uncontrolled server error.
- Dependencies are not fully pinned. TensorFlow is pinned to `2.20.0`, but
  OpenCV, XGBoost, scikit-learn, FastAPI, and Uvicorn are not version-pinned.
- `TTA_VIEWS` values that are odd or below two are not rejected; the view logic
  silently ignores an odd view or can produce no views.

## Accuracy-claim audit

The supplied README reports:

- Per-lesion accuracy: 91.70%.
- Per-image accuracy: 89.34% (described as 89.3% in the claimed confusion
  matrix).
- ROC-AUC: 0.938 per image and 0.952 per lesion.
- A claim that the HAM10000 test set was lesion-separated and never used for
  tuning.

No labels, predictions, confusion-matrix counts, evaluation script, split
manifest, lesion IDs, patient IDs, duplicate audit, threshold-selection
record, or confidence interval artifacts were included. Consequently:

- The 91.70% and 89.34% values cannot be recomputed.
- The positive class definition and ROC-AUC calculation cannot be independently
  verified.
- Per-image versus per-lesion aggregation cannot be checked against actual
  rows or lesion IDs.
- Train/validation/test separation, duplicate leakage, patient leakage, and
  test-set threshold selection remain unknown.
- The apparent 91.70% versus 89.34% discrepancy is plausibly explained by the
  README's stated change from per-image scoring to mean aggregation across
  same-lesion images, but this is only a description, not evidence.
- The 89.3% confusion-matrix figure is numerically consistent with the
  rounded 89.34% per-image claim, but the confusion-matrix cell counts were
  not supplied and cannot be audited.

No clinical validation conclusion is supported.

## Smoke-test status

Completed:

- ZIP inventory and source inspection.
- SHA-256 recording for the original archive and extracted files.
- Python syntax compilation of `app.py` and `inference.py` (`py_compile`
  passed).

Blocked:

- Isolated model-loading test: blocked because `backend_model.zip` and all
  checkpoint/config files are missing.
- `/health`, `/info`, and `/predict` tests for the supplied backend: blocked
  because startup requires absent model files.
- Valid/invalid/missing-image inference tests: blocked for the same reason.
- Accuracy recomputation: blocked because labels and predictions are absent.

The existing DermaVue frontend and backend were not changed or stopped. The
existing backend continues to report `503 model_unavailable` for analysis.

## Required before integration

1. Obtain the original `backend_model.zip` and its provenance, checksum, and
   license/usage terms.
2. Obtain the original evaluation script or a complete immutable evaluation
   bundle containing labels, predictions, split/lesion IDs, confusion-matrix
   counts, threshold-selection record, and dataset provenance.
3. Verify that model preprocessing, class order, metadata encoding, thresholds,
   and checkpoint hashes match the evaluation bundle.
4. Recompute image-level and lesion-level metrics without test-set tuning and
   audit patient/lesion overlap and duplicates.
5. Remediate API limits, validation, CORS, dependency pinning, and startup
   failure handling.
6. Design and review an adapter from `/predict` to the existing DermaVue
   `/api/cases/{case_id}/analyze` contract.
7. Only after those gates pass, create a separate approved release manifest;
   do not place the supplied model directly into the current serving path.
