# DermaVue: manuscript draft scaffold

This document remains a scaffold. The performance numbers below are copied
only from verified genuine experiment outputs and are not clinical claims.

## Abstract

Using the official HAM10000 release, the lesion-level five-class baseline
reached 0.7603 accuracy on 1,998 untouched test rows. A separately versioned
melanoma-versus-other-original-diagnosis task reached 0.8453 accuracy and
0.6547 melanoma sensitivity on 1,997 untouched rows. Neither result meets the
0.90 research target or establishes clinical validity.

## 1. Introduction

The current protocol investigates whether quality and cross-modal disagreement
can improve selective prediction behavior for genuinely paired skin-lesion
images. No paired dataset has yet been verified, so the executed result is
limited to a post-freeze single-image quality/selective-prediction analysis.

## 2. Related work

See [literature_matrix.md](../literature_review/literature_matrix.md). The
review currently indicates that multimodal fusion, attention, image quality,
calibration, abstention, and domain generalization are established areas.

## 3. Research gap and contribution

Pending expanded literature search and data feasibility audit. Do not claim
novelty yet.

## 4. Data, ethics, and provenance

The primary source is the official HAM10000 Harvard Dataverse release. The
license, checksums, source files, label mapping, and split reports are recorded
under `data/reports/` and `data/manifests/`. HAM10000 supplies lesion IDs but no
patient IDs or ground-truth skin-tone labels. Ethics/IRB, authorship, and
intended-use statements require manual author input.

## 5. Methods

The preserved V2 baseline and prepared training pipeline are documented in
`backend/model/v2_source/`, `experiments/v2_real_pipeline/`, and
`docs/V2_TRAINING_DATA_ACQUISITION_CHECKLIST.md`.

## 6. Experiments

The five-class baseline, binary task, validation-only classifier comparison,
and post-freeze quality/selective analysis are recorded under `experiments/`
and `results/`. Additional ablations, calibration comparisons, and external
validation remain pending. A post-hoc false-negative analysis and fixed
corruption robustness analysis are also recorded; neither was used for model
selection.

## 7. Results

Synthetic-demo results are excluded. Verified genuine results are reported in
the experiment-specific JSON files; the five-class and binary tasks must not be
compared as if they were the same classification problem. The binary model had
77 melanoma false negatives at threshold 0.5. A validation-selected threshold
of 0.30 reduced test false negatives to 40 and raised melanoma sensitivity to
0.8206, but reduced accuracy to 0.7626 and specificity to 0.7554. Fixed image
corruptions further reduced melanoma sensitivity, despite sometimes increasing
aggregate accuracy. These are research observations, not clinical claims.

## 8. Limitations and threats to validity

The HAM10000 study lacks patient identifiers, ground-truth skin-tone labels,
verified paired modalities, and external evaluation. ISIC 2020 has been
acquired, integrity-checked, and frozen as a separately versioned candidate;
no external result is reported because 1,187 perceptual overlap candidates
remain for review. A separately trained checkpoint now satisfies the exact
label contract for the task, but it is not an externally validated or serving
approved artifact.
The separately versioned ISIC task protocol uses a new genuine HAM10000
development cohort because the frozen ISIC external manifest leaves no
eligible labeled ISIC development rows. HAM10000 has no patient identifiers,
so lesion-level grouping is used; 222 HAM-side perceptual candidates are
withheld conservatively while the visual review remains incomplete. No
ISIC-contract checkpoint has yet been approved for serving.
MRA-MIDAS access remains restricted. Both current checkpoints are
research artifacts below the target and are not approved for serving. A
retrospective public-dataset study would not establish clinical validation.

## 9. Reproducibility and reporting

The final version will be audited against CLAIM 2024 and TRIPOD+AI. See
`docs/literature_review/literature_matrix.md` and the reproducibility checklist
to be completed after experiments.
