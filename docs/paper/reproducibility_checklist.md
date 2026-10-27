# Publication reproducibility checklist

Status: genuine HAM10000 baseline and binary experiment recorded; external and
clinical-validation items remain pending.

- [x] Dataset source, release, license, and checksum manifest.
- [x] Inclusion/exclusion criteria and label mapping for five-class and binary tasks.
- [x] Lesion-safe train, validation, and internal-test manifests; patient IDs and
  external-test data are unavailable.
- [ ] Exact source version and complete environment lock; runtime versions are
  recorded, but no package lockfile is committed.
- [x] Preprocessing, augmentation, seed, CPU hardware/runtime, and training
  configuration.
- [x] Validation-only model selection records.
- [x] Frozen test-set predictions, metrics, and bootstrap intervals for the
  binary task.
- [x] Melanoma-specific, calibration, selective-risk, false-negative, and
  fixed-corruption robustness results; ground-truth skin-tone subgroup and
  external results remain pending.
- [ ] Cross-source external evaluation, if compatible data is available.
- [x] Checkpoint, scaler, metadata pipeline, label mapping, and artifact checksums.
- [x] Checkpoint reload smoke test; backend serving parity remains intentionally
  unapproved.
- [x] Initial CLAIM 2024 and TRIPOD+AI guidance review recorded.
- [ ] Full reporting review and manuscript audit completed.
- [ ] Missing authorship, ethics, funding, conflicts, and clinical-partner details supplied by the research team.
