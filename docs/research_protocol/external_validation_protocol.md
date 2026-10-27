# External validation protocol: ISIC 2020 candidate

Protocol version: `isic2020_binary_melanoma_v1_external_eval_v1`  
Status: prepared; external evaluation has not been run.

## Research question

Can the frozen DermaVue image/metadata inference bundle produce reproducible
binary melanoma scores on a source-separated, patient-grouped dermoscopic
cohort that was not used for training, model selection, calibration, or
threshold selection?

This is an external-dataset performance question, not a clinical validation
or deployment study. The existing `binary_melanoma_other_dx_v1` task is not
silently relabeled: its negative class is the other HAM10000 diagnosis codes,
whereas this external candidate uses the official ISIC 2020 target
(`1=melanoma`, `0=non-melanoma`). A checkpoint trained for the former contract
must therefore pass an explicit compatibility review before it can be scored
on this task.

## Dataset and inclusion rules

- Source: official ISIC 2020 Challenge release, downloaded only from the
  official ISIC S3 link listed on the data portal.
- Modality: dermoscopic JPEG images.
- Required fields: image ID, patient ID, official binary target, diagnosis,
  sex, approximate age, and general anatomic site.
- Patient grouping: `patient_id`; the release does not supply a lesion ID in
  the acquired ground-truth table, so lesion-level independence is not
  asserted.
- Primary endpoint: rows with a non-`unknown` official diagnosis, complete
  patient ID, valid target in `{0,1}`, an available decodable image, and no
  official or exact-content duplicate exclusion.
- Rows with `diagnosis=unknown` are retained in `excluded_rows.csv` for
  accounting but are not part of the primary endpoint.
- All members of an official duplicate pair or exact-content duplicate group
  are excluded conservatively from the primary endpoint.
- No clinical image pairing is claimed. This release is dermoscopic only.
- No ground-truth skin-tone label is claimed; image-derived proxies are not
  subgroup labels.

## Leakage and overlap controls

1. The external manifest is frozen after acquisition and integrity validation.
2. It is evaluation-only: no training, feature selection, calibration,
   threshold selection, or model selection may read its labels.
3. Patient IDs are used for grouped bootstrap uncertainty.
4. Exact SHA-256 hashes are compared with the preserved HAM10000 manifests.
5. A DCT-based perceptual-hash review (Hamming distance threshold 4) identifies
   low-distance candidates. These are review evidence, not automatic proof of
   common provenance.
6. Any exact overlap is excluded and recorded. Unresolved provenance is
   reported as a limitation; it is not described as independent validation.

The overlap audit should use `all_rows.csv` when assessing source provenance;
the strict `external_evaluation.csv` is reserved for the primary endpoint.

## Model compatibility gate

Before any external scoring, verify and record:

- checkpoint/bundle hash and architecture;
- input size, color order, normalization, and deterministic preprocessing;
- required metadata fields and missing-value behavior;
- output label contract and probability meaning;
- whether the external modality matches the trained input;
- consistency of the saved feature names, metadata pipeline, classifier, and
  threshold with the original experiment.

If this gate fails, no external evaluation is performed. A compatible
adaptation must use a new task and version, with its own development data and
an untouched external manifest.

The check is reproducible with:

```powershell
py -3.12 scripts\research\assess_external_compatibility.py `
  --manifest data\manifests\isic2020_binary_melanoma_v1_external_eval\external_evaluation.csv `
  --bundle experiments\binary_melanoma\v1_mobilenetv2_fusion_seed42 `
  --out data\reports\isic2020_checkpoint_compatibility.json
```

## Metrics and uncertainty

The evaluator reports accuracy, sensitivity, specificity, precision, F1,
AUROC, AUPRC, Brier score, expected calibration error, confusion matrix,
class distribution, and patient-grouped bootstrap 95% intervals. Every output
records the dataset version, manifest hash, prediction hash, checkpoint hash,
configuration hash, timestamp, software version, threshold, and the explicit
statement that the external set was not used for selection.

## Reproduction

```powershell
py -3.12 scripts\research\prepare_isic2020_external_manifest.py `
  --metadata-csv data\raw\isic2020\ISIC_2020_Training_GroundTruth.csv `
  --duplicate-csv data\raw\isic2020\ISIC_2020_Training_Duplicates.csv `
  --images-dir data\raw\isic2020\images `
  --out-dir data\manifests\isic2020_binary_melanoma_v1_external_eval
```

```powershell
py -3.12 scripts\research\audit_external_overlap.py `
  --left-manifest data\manifests\isic2020_binary_melanoma_v1_external_eval\all_rows.csv `
  --left-name isic2020_all `
  --right-manifest data\manifests\ham10000_v4_seed42\train.csv `
  --right-manifest data\manifests\ham10000_v4_seed42\validation.csv `
  --right-manifest data\manifests\ham10000_v4_seed42\test.csv `
  --right-name ham10000_v4_all `
  --out data\reports\isic2020_ham10000_overlap_dct.json
```

The completed audit found 0 exact cross-dataset image-hash matches and 1,187
DCT candidates requiring manual review. External scoring is intentionally not
run until those candidates are dispositioned and the compatibility gate passes
with a prediction file from the unchanged, compatible checkpoint.

## Manual review workflow

Initialize the separate versioned review file:

    py -3.12 scripts/research/manual_overlap_review.py init --audit data/reports/isic2020_ham10000_overlap_dct.json --left-manifest data/manifests/isic2020_binary_melanoma_v1_external_eval/all_rows.csv --right-manifest data/manifests/ham10000_v4_seed42/train.csv --right-manifest data/manifests/ham10000_v4_seed42/validation.csv --right-manifest data/manifests/ham10000_v4_seed42/test.csv --out data/reports/isic2020_ham10000_overlap_review_v1.json

Run the standalone research interface and resume it whenever needed:

    py -3.12 scripts/research/manual_overlap_review.py serve --review-file data/reports/isic2020_ham10000_overlap_review_v1.json

Summarize only explicit decisions:

    py -3.12 scripts/research/manual_overlap_review.py summarize --audit data/reports/isic2020_ham10000_overlap_dct.json --review-file data/reports/isic2020_ham10000_overlap_review_v1.json --out data/reports/isic2020_ham10000_overlap_review_v1_report.json

The current review file contains 1,187 unreviewed candidates. It does not
claim that any perceptual pair is a duplicate.
