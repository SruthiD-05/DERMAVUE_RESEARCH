# V2 genuine-data training and evaluation checklist

Status date: 2026-10-01  
Workspace: `F:\SkinCancer`

This checklist records the inputs and evidence required before the DermaVue
analysis button may be enabled. The 90% accuracy goal is a research target,
not a reason to alter a split, use synthetic data, or select a model from the
test set.

## Current audit

### Present in this workspace

- [x] The complete V2 source tree is preserved at
  `backend/model/v2_source/src/`.
- [x] The original binary/demo pipeline is present: `train.py`, `dataset.py`,
  `cnn_model.py`, `handcrafted_features.py`, `segmentation.py`,
  `preprocessing.py`, `fusion_classifier.py`, and `evaluate.py`.
- [x] The real-data pipeline source is present: `train_real.py`,
  `real_dataset.py`, `metadata_features.py`, `skin_tone_proxy.py`, and the
  multiclass additions in `cnn_model.py`, `fusion_classifier.py`, and
  `evaluate.py`.
- [x] The source defines a five-category HAM10000 mapping in
  `metadata_features.py`: `nv` → Normal Skin; `bkl`/`df` → Skin Allergy/Acne;
  `vasc`/`akiec` → Suspicious Lesion; `bcc` → Basal Cell Carcinoma; `mel` →
  Melanoma.
- [x] Synthetic demo images and synthetic-only experiment outputs are present
  under `experiments/v2_original_baseline/` and
  `experiments/v2_mobilenetv2/`.
- [x] The synthetic MobileNetV2 bundle includes
  `experiments/v2_mobilenetv2/outputs/cnn_branch.keras`,
  `fusion_classifier.joblib`, `experiment_config.json`, and summary files.
  These artifacts are explicitly **not** eligible for clinical inference.
- [x] The backend safety adapter and frontend unavailable-model behavior are
  active and must remain active until all release gates below pass.
- [x] Preparation-only configuration, grouped manifest validation, and guarded
  evaluation tooling are available under `experiments/v2_real_pipeline/` and
  `scripts/v2/`.
- [x] A prepared inference contract is documented in
  `docs/V2_INFERENCE_CONTRACT.md`; serving remains disabled.
- [x] An official HAM10000 release was acquired from Harvard Dataverse and
  recorded in `data/reports/ham10000_acquisition.md`.
- [x] Genuine HAM10000 archives, metadata, and extracted images are present
  under `data/raw/ham10000/` and `data/processed/ham10000/` with recorded
  checksums.
- [x] Deterministic lesion-level manifests are present under
  `data/manifests/ham10000_v4_seed42/`; the test manifest has 1,998 rows and
  was kept out of model selection.
- [x] A genuine baseline bundle and standalone test evaluation are present at
  `experiments/baselines/v2_real_ham10000_v4_seed42/` and
  `results/v2_real_ham10000_v4_seed42/`.
- [x] A separately versioned binary task is present under
  `data/manifests/ham10000_binary_melanoma_other_dx_v1_seed42/`, with its
  class mapping, validation-only selection record, and test evaluation under
  `experiments/binary_melanoma/` and `results/`.

### Missing or not verified

- [x] The primary HAM10000 genuine dataset, metadata, image directories,
  provenance, terms record, and acquisition checksums are present. A patient
  identifier is not present in the official metadata, so patient-level
  leakage cannot be audited for this release.
- [x] A fixed, reviewable lesion-level train/validation/test manifest exists.
- [x] A genuine-data baseline directory exists with a CNN checkpoint, fused
  classifier, fitted scaler, metadata transformer, metrics, predictions, and
  an artifact checksum manifest. It is an experiment output, not a serving
  release.
- [ ] No genuine-data bundle is validated and approved for backend serving.
- [ ] No backend-compatible real-data inference contract has been validated.
- [x] Genuine-data test metrics were generated without test-set model
  selection, but they do not support a 90% claim: the baseline accuracy was
  `0.7602602603` on 1,998 held-out rows.
- [ ] No paired clinical/dermoscopic dataset has been verified for the planned
  reliability/selective-prediction study.
- [x] A post-freeze quality/selective-prediction analysis was run on the
  binary test predictions; it was not used for training, feature selection, or
  threshold tuning.
- [x] False-negative, validation-only threshold, calibration, and fixed-
  corruption analyses are recorded separately; none enabled serving or
  changed the historical test artifacts.
- [x] Official ISIC 2020 ground-truth, duplicate-list, and JPEG archive are
  acquired under `data/raw/isic2020/`; the archive length and SHA-256 are
  recorded in `data/raw/isic2020/acquisition_manifest.json`.
- [x] External-validation protocol, acquisition plan, patient-grouped
  evaluator, and exact/perceptual overlap tooling are present under
  `docs/research_protocol/` and `scripts/research/`.
- [x] ISIC 2020 archive extraction, image integrity report, frozen candidate
  manifest, exact cross-dataset overlap audit, and checksum records are
  complete. The archive has 33,126 decoded images, 0 missing/extra files, and
  0 exact SHA-256 matches against the preserved HAM10000 manifests.
- [ ] 1,187 DCT perceptual-overlap candidates (Hamming distance <=4) have
  completed manual provenance review; they remain unresolved and prevent an
  unqualified independent-validation claim.
- [x] A separately versioned checkpoint with the ISIC 2020
  melanoma-versus-non-melanoma label contract has been trained and reloaded:
  `experiments/isic2020_melanoma_vs_nonmelanoma_v1/ham10000_cpu128_seed42/`.
  It is compatible for research evaluation, but is not approved for backend
  serving or external reporting while overlap review remains incomplete.
- [x] A versioned ISIC task configuration and leakage-resistant training
  protocol are recorded under
  `experiments/isic2020_melanoma_vs_nonmelanoma_v1/` and
  `docs/research_protocol/isic2020_model_development_protocol.md`.
- [x] A resumable side-by-side review utility and versioned review file exist
  for all 1,187 perceptual candidates.
- [ ] A labeled ISIC development cohort remains available after excluding the
  frozen external manifest, official/exact duplicates, and conservative
  unresolved-overlap candidates. Current eligible count: 0.
- [x] A separate genuine HAM10000 development cohort was prepared for the new
  ISIC-contract task: 6,641 train rows, 1,153 validation rows, lesion-level
  grouping, and 222 HAM-side perceptual candidates withheld conservatively.
- [x] A new ISIC-contract checkpoint has been trained, reloaded, and frozen
  for internal validation. The restored-best validation accuracy was
  `0.7189939022` and AUROC was `0.8357337117`; these are not external metrics
  and do not establish the 90% goal.

### Current reproducible binary-task run

The completed genuine-data command is:

```powershell
py -3.12 experiments/isic2020_melanoma_vs_nonmelanoma_v1/train_prepared.py --train-manifest data/manifests/isic2020_melanoma_vs_nonmelanoma_v1_ham_development/train.csv --validation-manifest data/manifests/isic2020_melanoma_vs_nonmelanoma_v1_ham_development/validation.csv --external-manifest data/manifests/isic2020_binary_melanoma_v1_external_eval/external_evaluation.csv --config experiments/isic2020_melanoma_vs_nonmelanoma_v1/config_cpu128_seed42.json --out-dir experiments/isic2020_melanoma_vs_nonmelanoma_v1/ham10000_cpu128_seed42
```

The run artifact is
`experiments/isic2020_melanoma_vs_nonmelanoma_v1/ham10000_cpu128_seed42/`.
It contains the reloaded MobileNetV2 checkpoint, training log, runtime
record, label mapping, configuration, and artifact hashes. External
prediction and evaluation commands are intentionally blocked until all 1,187
overlap candidates have reviewed dispositions with no unresolved uncertainty.

## What must be obtained

### 1. Dataset package and provenance

- [x] Obtain the full genuine HAM10000 labeled release, with the original
  source and version recorded.
- [x] Record the published non-commercial terms and attribution requirements;
  institutional compliance and any redistribution decision remain pending.
- [x] Record the official file checksums, download URLs, retrieval time, and
  release/version in `data/raw/ham10000/acquisition_manifest.json`.
- [x] Record the dataset paper and labeling/provenance documentation in
  `data/reports/ham10000_acquisition.md` and
  `data/reports/provenance/ham10000_v4.json`.
- [x] Store readable JPEG images with stable IDs matching the metadata.
- [x] Store the complete required metadata columns for the current pipeline;
  unknown patient identity remains unavailable rather than inferred.
- [ ] Provide patient IDs if available. If multiple lesions belong to one
  patient, patient identity must be retained for the split audit even when it
  is not passed as a model feature. HAM10000's supplied metadata does not
  provide this field.
- [ ] Provide skin-tone/Fitzpatrick labels if they genuinely exist. If they do
  not, document that the current ITA estimate is only a proxy and cannot be
  reported as ground-truth skin tone.

### 2. Task and label contract

The current code contains two different contracts. Before training, choose and
document one; do not mix their labels or checkpoints.

- [x] **Preferred existing real-data contract:** five-class HAM10000-style
  classification using the `RISK_CATEGORIES` order in
  `metadata_features.py`. The requested 90% threshold must then be defined as
  overall five-class test accuracy, with macro-F1 and melanoma per-class
  sensitivity reported alongside it.
- [ ] If a binary benign/melanoma task is required instead, obtain binary
  labels and a documented mapping and use a separately versioned binary
  experiment. Do not present the current synthetic binary checkpoint as a
  five-class model.
- [x] The separately versioned binary task uses `mel` versus the other
  original HAM10000 `dx` labels and explicitly does not call the negative class
  benign. It is not clinically equivalent to a complete skin-cancer workflow.
- [x] Confirm the current evaluation unit (image rows grouped by lesion), the
  exact primary metric (overall five-class accuracy), and the 0.90 target in
  the prepared configuration. The broader target-population/clinical-use
  claim remains research-only and is not a clinical validation claim.
- [x] Define minimum safety metrics in advance: melanoma sensitivity, macro-F1,
  specificity, AUROC, and minimum support per class. Overall accuracy alone is
  insufficient.

### 3. Leakage-safe split package

- [x] Create immutable train/validation/test manifests from the genuine data
  using patient-level splitting where patient IDs are available; otherwise use
  lesion-level splitting via `lesion_id`.
- [x] Ensure every image from one lesion stays in exactly one split. Verify that
  no patient crosses splits when patient IDs exist.
- [x] Use a fixed seed and save the seed, split algorithm, package version, and
  exact row/image IDs in each manifest.
- [x] Keep the test manifest read-only after creation. No threshold, backbone,
  augmentation, class cap, or classifier decision may be tuned using test
  metrics.
- [x] Record class counts, lesion counts, missing-image checks, and exact
  duplicate hashes, and metadata availability for all three splits.
- [x] Confirm that every class has nonzero test support; the smallest class has
  93 rows. Whether this is adequate for a stronger clinical reliability claim
  remains a limitation rather than a reason to oversample.

### 4. Reproducible training inputs and configuration

- [x] Save the exact Python version, TensorFlow version, and CPU-only runtime
  details for the completed baseline; a complete package lockfile remains
  pending.
- [x] Save the exact V2 preprocessing configuration: image size, color handling,
  normalization, hair removal/denoising, segmentation parameters, and any
  augmentation. Augmentation must run only on training data.
- [x] Save the backbone choice (`scratch` or MobileNetV2), ImageNet-weight
  provenance if used, frozen/fine-tuned layers, epochs, batch size, optimizer,
  learning-rate schedule, class weights, sampling caps, and random seeds.
- [x] Fit scalers, imputers, one-hot encoders, and other transforms on training
  data only; serialize each fitted artifact.
- [x] Select the model and all hyperparameters using training/validation data
  only. Preserve every experiment configuration and validation result.

### 4A. External evaluation package

- [x] Record the official ISIC 2020 source, terms URL, release links, and
  citation requirements.
- [x] Preserve the official ground-truth and duplicate-list files without
  relabeling or pooling.
- [x] Define a separate binary external task with patient-grouped evaluation,
  strict exclusion of unknown diagnoses from the primary endpoint, and no
  external-set model selection.
- [x] Add acquisition checksum, manifest-generation, overlap-audit, and
  patient-grouped metric tooling.
- [x] Complete archive download, extract and decode all images, generate the
  frozen candidate manifest, and record all integrity and overlap findings.
- [ ] Run an external evaluation. This remains blocked until checkpoint
  architecture, preprocessing, metadata, modality, and label compatibility
  are explicitly verified.

### 5. Required genuine-data output bundle

The final candidate is not complete unless all of the following are saved in a
versioned directory such as `experiments/v2_real/outputs/`:

- [x] CNN checkpoint for the exact selected architecture.
- [x] Fused classifier (`joblib` or equivalent) and fitted feature scaler.
- [x] Fitted metadata preprocessing pipeline, when the metadata branch is used.
- [x] Exact preprocessing and segmentation configuration.
- [x] Ordered label mapping and class names.
- [x] Feature-name lists and branch dimensions.
- [x] Immutable train/validation/test manifests and artifact checksums.
- [x] Training history, validation model-selection table, and experiment
  configuration.
- [x] Final untouched-test metrics: accuracy, balanced accuracy, macro-F1,
  sensitivity/recall, specificity, precision, AUROC, per-class report, and
  confusion matrix.
- [x] Class and split distributions, including lesion counts; patient counts
  remain unavailable for HAM10000.
- [x] Skin-tone subgroup results using the documented ITA-based proxy;
  otherwise label the current ITA-based values as a proxy.
- [x] A checksum for every generated artifact and a record identifying the
  baseline bundle are present. The bundle is not selected for serving because
  the evaluation gate is not passed.

## Evaluation release gate

The model may be called “validated for this research evaluation” only when all
of these are true:

- [x] Genuine-data provenance and license are documented.
- [x] The untouched test set is lesion-leakage-free and its manifest is
  frozen before final scoring.
- [x] The selected model was chosen without test-set tuning.
- [ ] The exact reported candidate reaches the predeclared 90% test-accuracy
  target, if that target is still scientifically appropriate.
- [x] Macro-F1, melanoma sensitivity, specificity, AUROC, per-class results,
  confusion matrix, and subgroup results are acceptable and disclosed even if
  accuracy is at least 90%. The current results are disclosed but do not meet
  the target or establish clinical acceptability.
- [x] If the target is missed, the actual results and limitations are reported;
  no split or label changes are made to force a pass.
- [ ] A clean reload test reproduces predictions from the saved checkpoint and
  serialized preprocessing artifacts.

## Integration gate

Keep `backend/app/model_adapter.py` unavailable and the frontend analysis flow
disabled until every evaluation gate above passes. Then, and only then:

- [ ] Implement the adapter against the exact saved real-data bundle.
- [ ] Confirm backend preprocessing and label mapping byte-for-byte against the
  evaluated configuration.
- [ ] Add API tests for valid inputs, missing images, invalid MIME types,
  missing artifacts, malformed metadata, and inference failures.
- [ ] Verify that the backend loads the same checkpoint checksum recorded in the
  evaluation report.
- [ ] Run an end-to-end upload → inference → stored result → frontend display
  test using a non-test validation fixture.
- [ ] Update the model report and API documentation before enabling analysis.

## Explicit non-goals

- Do not copy the synthetic `cnn_branch.keras` or synthetic fusion classifier
  into `backend/model/artifacts/`.
- Do not use synthetic 100% results as evidence for the genuine 90% target.
- Do not reconstruct missing patient/lesion IDs, labels, metadata, or metrics.
- Do not tune against the held-out test set or repeatedly re-split until the
  target is reached.
