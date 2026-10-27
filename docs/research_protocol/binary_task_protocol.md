# Binary melanoma task protocol

Task version: `binary_melanoma_other_dx_v1`  
Dataset: official HAM10000 release, Dataverse version 4  
Split seed: 42  
Grouping: `lesion_id` because no patient identifier is supplied

## Label definition

`mel` is the positive class. The negative class contains the other original
HAM10000 diagnosis codes (`nv`, `bkl`, `df`, `vasc`, `akiec`, `bcc`). It is
named `Non-melanoma (other HAM10000 dx)` to avoid implying that these cases are
benign, cancer-free, or clinically interchangeable. Original `dx` values remain
available for error analysis.

## Split and selection protocol

The binary manifests are independently generated and immutable under
`data/manifests/ham10000_binary_melanoma_other_dx_v1_seed42/`:

- train: 6,830 rows;
- validation: 1,186 rows;
- test: 1,997 rows, defined before training and never used for selection.

Because both tasks use HAM10000, 474 binary-test image IDs overlap the
historical five-class test manifest. This is a separate task split, not an
independent external cohort; no five-class test outputs were used for binary
selection or tuning.

The configured experiment uses a class-weighted MobileNetV2 branch with V2
handcrafted and metadata fusion. SVM, Random Forest, and XGBoost candidates are
fit on training data and selected by validation AUROC. The threshold is fixed
at 0.5 for this version; no test-derived threshold was used.

## Reporting

Required metrics are accuracy, balanced accuracy, macro/weighted F1, melanoma
sensitivity, melanoma specificity, precision, AUROC, AUPRC, Brier score,
expected calibration error, confusion matrix, false negatives, and bootstrap
95% intervals. The current result is recorded in
`results/binary_melanoma_other_dx_v1_seed42/evaluation.json`.

This task is a research projection of HAM10000 labels, not a complete skin
cancer diagnostic workflow and not a clinical validation study.
