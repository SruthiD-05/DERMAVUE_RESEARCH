# DermaVue Final Accuracy and Classification Audit

Date: 2026-10-25

## Executive result

The supplied partner evaluation rows reproduce the previously reported **91.7038% lesion-level accuracy**, but the corresponding image-level accuracy is **89.3377%**, below the 90% goal. This is not evidence of general clinical performance: patient-level independence cannot be established from the supplied artifacts, and the partner train/validation manifests and patient identifiers were not supplied. The release gate remains disabled.

`evaluation_gate_passed=false` and `serving_enabled=false` remain unchanged.

## Recomputed partner metrics

Metrics were calculated directly from `incoming/teammate_final_package_audit/results/test_predictions.csv` and `test_predictions_per_lesion.csv`. Positive class is the partner's documented malignant grouping (`mel`, `bcc`, `akiec`).

| Unit | N | Correct | Accuracy | Confusion matrix `[[TN,FP],[FN,TP]]` | Precision | Sensitivity/Recall | Specificity | F1 | AUROC |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| Image | 1510 | 1349 | 89.3377% | `[[1170,53],[108,179]]` | 0.7716 | 0.6237 | 0.9567 | 0.6898 | 0.9334 |
| Lesion aggregate | 1121 | 1028 | 91.7038% | `[[916,30],[63,112]]` | 0.7887 | 0.6400 | 0.9683 | 0.7066 | 0.9522 |

The discrepancy is therefore real and is explained by the supplied lesion-level aggregation: repeated lesion groups contribute multiple image rows but one lesion decision. The seven-class values in the files are diagnosis labels/source metadata, not seven-class predictions. A seven-class subtype accuracy, macro-F1, or multiclass AUROC cannot be computed from this package.

The release manifest separately records raw image accuracy as **0.8973509933774835 (89.7351%)**. That value does not match the direct CSV recomputation above (89.3377%); the manifest value is therefore treated as an unverified reported value, not as the audit result. The manifest's AUROC (0.9334432) is consistent with the direct recomputation to rounding.

## Integrity and leakage checks

- 1510 unique image IDs and 1121 unique lesion IDs were present.
- 296 lesion groups repeat in the image table; the largest group has five images.
- All 1510 test files were located in the local HAM10000 processed image parts.
- The test rows contain 1510 unique SHA-256 hashes; no duplicate hash groups were found within the test set.
- Two duplicate hash groups exist in the broader local source inventory, but none include these test hashes.
- The supplied test CSV contains no patient IDs. Patient-level independence cannot be verified.
- Overlap with local HAM manifests was observed, but those manifests represent the same HAM universe and do not establish the partner train/test boundary. The partner train/validation manifests were not supplied.

## Other genuine project evaluations

For context, the separate five-class V2 baseline has 1998 test rows and 1519 correct (76.0260% accuracy; macro-F1 0.5327). The separate binary melanoma-vs-other experiment has 1997 rows and 84.5268% accuracy. These are different tasks and checkpoints and must not be combined with the partner binary result.

## Classification UI change

`frontend/components/results/results-view.tsx` now keeps the fused binary result separate from the seven auxiliary CNN scores and dynamically selects a unique highest valid auxiliary score. It displays the full class name and score under **Top-scoring subtype**, explicitly labels it as an auxiliary score rather than a confirmed diagnosis, handles ties and missing/invalid scores, and states that it does not override the fused result.

The live research smoke response returned seven scores and selected `nv` / **Melanocytic nevus** at approximately 97.1% as the top auxiliary score, while the fused result remained `BENIGN` with a malignancy score of approximately 1.35%. This is a software smoke result, not a clinical diagnosis or accuracy result.

## Verification executed

- Frontend `pnpm exec tsc --noEmit`: passed.
- Frontend `pnpm build`: passed; production routes generated.
- Backend `py -3 -m unittest backend.test_partner_adapter backend.test_model_safety -v`: 7 tests passed.
- Backend `py -3 -m py_compile backend/app/server.py backend/app/partner_adapter.py`: passed.
- Real loopback research inference on an authorized HAM10000 image: HTTP 200; binary response, seven auxiliary scores, disclaimer, and dynamic top-score data returned.
- Frontend remained running on `http://127.0.0.1:3000`; backend research endpoint remained on `http://127.0.0.1:8000`.

## Limitations and release status

The supplied evidence does not establish patient-independent external validation, clinical validation, or a guaranteed 90% target. The partner model is binary at its final output; auxiliary seven-class CNN scores are not validated probabilities and do not constitute subtype diagnosis. No model weights, thresholds, release flags, research datasets, or existing experiments were changed in this audit.

The next release action is to provide the missing partner train/validation manifests with patient identifiers and provenance, independently verify duplicate and patient/lesion separation, and obtain an approved untouched genuine evaluation before changing the release decision. Until then, production analysis must remain gated at `503 model_unavailable`.
