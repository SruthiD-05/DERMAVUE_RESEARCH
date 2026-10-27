# ISIC 2020 model-development protocol

Protocol version: isic2020_melanoma_vs_nonmelanoma_v1  
Status: genuine HAM10000 development run completed for internal validation;
ISIC-only development remains blocked and external evaluation remains gated.

## Research question

Can a reproducible dermoscopic model trained under the official ISIC binary
contract distinguish melanoma (1) from official non-melanoma (0) on an
untouched, patient-grouped external cohort? The 90% external accuracy value is
a research goal, not a guaranteed result.

## Data and split rules

- Development source: official HAM10000 Dataverse version 4, already acquired
  and checksum-recorded in the project.
- Evaluation source: official ISIC 2020 Challenge release and recorded
  acquisition manifest.
- Modality: dermoscopic images for both sources.
- Labels: only the source target field; 0=official non-melanoma,
  1=melanoma.
- Exclude diagnosis=unknown; no unknown row is relabeled.
- Exclude every official duplicate-pair and exact-content duplicate member.
- The ISIC frozen external-evaluation rows are never pooled into development.
- Exclude confirmed cross-dataset overlaps. While perceptual candidates remain
  unresolved, the default conservative policy excludes their HAM10000 members
  from development.
- Group train/validation by patient_id where available. HAM10000 supplies no
  patient identifier, so the prepared development manifests use lesion_id.
- Keep the frozen external manifest immutable and evaluation-only.

The ISIC-only source has 6,002 non-unknown labeled rows. The frozen external
manifest contains 5,988; the remaining 14 labeled rows are duplicate
exclusions, so an ISIC-only development split is impossible without
redesigning the frozen release. The selected valid path is the separate
HAM10000 development cohort, which has 6,641 training rows and 1,153
validation rows after withholding 222 HAM-side perceptual candidates. Its
preserved 1,997-row test split remains untouched.

When a new eligible development source is available, the prepared trainer is
invoked only with new train/validation manifests:

    py -3.12 experiments/isic2020_melanoma_vs_nonmelanoma_v1/train_prepared.py --train-manifest data/manifests/isic2020_melanoma_vs_nonmelanoma_v1_development/train.csv --validation-manifest data/manifests/isic2020_melanoma_vs_nonmelanoma_v1_development/validation.csv --external-manifest data/manifests/isic2020_binary_melanoma_v1_external_eval/external_evaluation.csv --config experiments/isic2020_melanoma_vs_nonmelanoma_v1/config.json --out-dir experiments/isic2020_melanoma_vs_nonmelanoma_v1/seed42

## Baseline configuration

The versioned configuration is
experiments/isic2020_melanoma_vs_nonmelanoma_v1/config.json:

- ImageNet-pretrained MobileNetV2, frozen backbone initially, 224x224 RGB.
- TensorFlow MobileNetV2 preprocessing and training-only augmentation.
- Sigmoid binary head, binary cross-entropy, Adam, balanced class weights.
- Seed 42, batch size 32, maximum 30 epochs.
- Validation-only AUROC selection, early stopping, and calibration/threshold
  decisions. The external set is never used for these decisions.
- Checkpoints, CSV logs, runtime package versions, config, label mapping, and
  artifact hashes are saved in a new experiment directory.

For the current CPU-only genuine-data run, the explicitly named efficient
variant is
experiments/isic2020_melanoma_vs_nonmelanoma_v1/config_cpu128_seed42.json.
It keeps the same task, labels, preprocessing family, frozen ImageNet
MobileNetV2, seed, and validation-only model selection while using 128x128
inputs, batch size 64, and a 12-epoch ceiling. The earlier 224x224 run is
preserved as an interrupted experiment and is not treated as an authoritative
checkpoint.

The completed genuine-data training command was:

    py -3.12 experiments/isic2020_melanoma_vs_nonmelanoma_v1/train_prepared.py --train-manifest data/manifests/isic2020_melanoma_vs_nonmelanoma_v1_ham_development/train.csv --validation-manifest data/manifests/isic2020_melanoma_vs_nonmelanoma_v1_ham_development/validation.csv --external-manifest data/manifests/isic2020_binary_melanoma_v1_external_eval/external_evaluation.csv --config experiments/isic2020_melanoma_vs_nonmelanoma_v1/config_cpu128_seed42.json --out-dir experiments/isic2020_melanoma_vs_nonmelanoma_v1/ham10000_cpu128_seed42

## Evaluation

After the model and operating threshold are frozen, a separate prediction
file may be generated for the frozen external manifest and passed to
scripts/research/evaluate_external_predictions.py. The evaluator records
the manifest, prediction, checkpoint, configuration, and software hashes and
reports accuracy, sensitivity, specificity, precision, F1, AUROC, AUPRC,
Brier score, calibration error, confusion matrix, false negatives/positives,
and patient-grouped bootstrap intervals.

No external prediction or metric is valid until the overlap review, compatible
checkpoint, preprocessing, and label-contract gates pass. The prediction and
evaluation entry points require the completed overlap-review report and refuse
to run while any candidate is unreviewed or uncertain.

After a checkpoint is frozen, prediction generation and evaluation remain
separate:

    py -3.12 scripts/research/predict_isic2020_task.py --manifest data/manifests/isic2020_binary_melanoma_v1_external_eval/external_evaluation.csv --checkpoint experiments/isic2020_melanoma_vs_nonmelanoma_v1/ham10000_cpu128_seed42/checkpoint_best.keras --config experiments/isic2020_melanoma_vs_nonmelanoma_v1/config_cpu128_seed42.json --overlap-review-report data/reports/isic2020_ham10000_overlap_review_v1_report.json --out results/research/isic2020_melanoma_vs_nonmelanoma_v1/ham10000_cpu128_seed42_external_predictions.csv

    py -3.12 scripts/research/evaluate_external_predictions.py --manifest data/manifests/isic2020_binary_melanoma_v1_external_eval/external_evaluation.csv --predictions results/research/isic2020_melanoma_vs_nonmelanoma_v1/ham10000_cpu128_seed42_external_predictions.csv --checkpoint experiments/isic2020_melanoma_vs_nonmelanoma_v1/ham10000_cpu128_seed42/checkpoint_best.keras --config experiments/isic2020_melanoma_vs_nonmelanoma_v1/config_cpu128_seed42.json --overlap-review-report data/reports/isic2020_ham10000_overlap_review_v1_report.json --out-dir results/research/isic2020_melanoma_vs_nonmelanoma_v1/ham10000_cpu128_seed42_evaluation --threshold 0.5

## Limitations

ISIC 2020 supplies patient IDs but no lesion IDs, paired clinical images, or
ground-truth skin-tone labels. Age and anatomical site can be described only
where recorded; image-derived skin-tone proxies are not subgroup labels.
Retrospective dataset performance is not clinical validation, fairness
evidence, or deployment authorization.
