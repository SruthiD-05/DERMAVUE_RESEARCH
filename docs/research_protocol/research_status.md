# DermaVue research status

Status date: 2026-10-01

## Completed in this phase

- Audited the preserved V2 source, synthetic experiments, frontend, backend,
  and existing data-acquisition checklist.
- Created the research directory layout without moving or overwriting existing
  experiments.
- Completed an initial focused literature review and recorded the search scope,
  dataset candidates, competing methods, and novelty decision.
- Rejected standalone multimodal fusion and attention as sufficient novelty.
- Defined a bounded research question around quality-conditioned disagreement and
  selective prediction, conditional on genuinely paired data.
- Added genuine-data validation, duplicate review, fixed grouped manifests,
  validation-only model selection, guarded evaluation, and artifact packaging.
- Prepared the backend release-manifest gate while keeping inference disabled.
- Added paper and reproducibility scaffolds with explicit pending placeholders.
- Acquired and checksum-verified the official HAM10000 release (Dataverse
  version 4), extracted it without deleting the raw archives, and produced a
  lesion-level five-class manifest.
- Ran the genuine baseline from the frozen manifests and independently
  reevaluated its untouched test predictions. The result was 0.7602602603
  accuracy on 1,998 rows, below the 0.90 research target.
- Kept the backend model-unavailable gate active; the genuine baseline is an
  experiment artifact and is not a serving release.
- Defined and executed the separately versioned binary task
  `binary_melanoma_other_dx_v1`: `mel` versus the other original HAM10000
  diagnosis codes, explicitly not a benign-versus-cancer clinical contract.
- Compared SVM, Random Forest, and XGBoost fusion candidates using validation
  AUROC only. Random Forest was selected and evaluated once on the separate
  frozen binary test manifest.
- Added post-freeze genuine-image quality descriptors and fixed risk-coverage
  analysis; no quality feature or selective threshold was used to tune the
  binary model.
- Completed post-hoc analysis of all 77 binary melanoma false negatives with
  grouped uncertainty, available metadata, quality proxies, and confidence
  distributions.
- Defined a validation-only threshold protocol. Threshold 0.30 raised test
  melanoma sensitivity to 0.8206 and reduced false negatives to 40, but test
  accuracy fell to 0.7626 and specificity to 0.7554; it is not a clinical
  recommendation.
- Completed fixed post-freeze blur, noise, brightness, and JPEG robustness
  analyses. Every corruption reduced melanoma sensitivity despite some higher
  aggregate accuracy values.
- Audited official external sources and selected ISIC 2020 as a separately
  versioned public candidate for external evaluation. Its ground-truth file,
  official duplicate list, and JPEG archive are acquired and SHA-256 recorded
  under `data/raw/isic2020/`; all 33,126 images are extracted and decoded.
- Added a patient-grouped external manifest validator, immutable acquisition
  record generator, exact/perceptual overlap audit, and hash-recording
  external evaluator. These tools do not train or tune a model.
- Added a resumable side-by-side visual review utility for all 1,187 DCT
  candidates. Its new versioned review file currently records all candidates
  as unreviewed; no duplicate decisions were fabricated.
- Defined the separately versioned ISIC task
  `isic2020_melanoma_vs_nonmelanoma_v1`, its MobileNetV2 baseline protocol,
  training safeguards, prediction contract, and development-readiness
  manifest.
- Prepared and trained the genuine HAM10000 development path for that exact
  task using `config_cpu128_seed42.json`: 6,641 train rows, 1,153 validation
  rows, lesion-level grouping, and no use of the preserved HAM test or ISIC
  labels. The checkpoint reload passed; validation accuracy was 0.7189939022
  and validation AUROC was 0.8357337117.
- Added streaming external prediction and evaluation gates that require a
  completed overlap review and reject the current incomplete report before
  creating predictions or metrics.

## Blocked

- No patient identifiers or ground-truth skin-tone labels are supplied in the
  HAM10000 release, so patient-level and ground-truth skin-tone audits remain
  unavailable.
- The baseline misses the 0.90 accuracy target and is not validated for
  serving.
- The binary result also misses the target: 0.8453 accuracy, 0.6547 melanoma
  sensitivity, and 0.8672 AUROC on 1,997 held-out rows.
- No serving-approved checkpoint or release manifest exists. The new research
  checkpoint is compatible with the exact task contract but is not released.
- No paired clinical/dermoscopic dataset has been verified for the proposed
  reliability study.
- MRA-MIDAS remains access-controlled through the official Stanford/Redivis
  portal; no credentials or institutional authorization are available in this
  workspace, so it was not bypassed or downloaded.
- ISIC 2020 external evaluation remains blocked by unresolved perceptual
  overlap candidates (1,187 at DCT Hamming distance <=4). Exact
  cross-dataset image-hash overlap is 0. A new compatible research checkpoint
  now exists, but the external prediction/evaluation gate correctly refuses to
  run until the overlap review is complete.
- The new ISIC development task is blocked before training: 6,002 labeled
  non-unknown rows exist, 5,988 are frozen external rows, and the remaining
  14 are official/exact duplicate exclusions. The ISIC-only development path
  is unavailable, so the separately acquired HAM10000 release is being used
  as a new genuine development source under the exact ISIC output contract.

## Next action requiring external input

Use the new review utility to disposition the perceptual overlap candidates.
The current protocol conservatively excludes their HAM10000 members from
development. After the review is complete, verify the frozen checkpoint and
run the gated external prediction/evaluation commands. Keep backend serving
disabled until the external gates and release-manifest review pass.
Obtain MRA-MIDAS only through the official
access/authorization process if paired modality analysis is required. Do not
enable frontend analysis from either current baseline.
