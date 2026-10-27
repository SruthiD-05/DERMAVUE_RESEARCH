# DermaVue Model Integration Report

Date: 2026-10-25  
Status: **Integrated as a release-gated compatibility adapter; live analysis remains disabled**

## Outcome

The audited partner package is available in the isolated, versioned directory
`backend/model/artifacts/teammate_partner_v1/`. A lazy backend adapter now
preserves the partner preprocessing, metadata inputs, thresholds, and
multi-image aggregation contract. It maps only values actually returned by
the partner API and rejects invalid ranges or categories.

The production release is not approved. The manifest deliberately contains
`evaluation_gate_passed: false` and `serving_enabled: false`, so
`POST /api/cases/{case_id}/analyze` continues to return `503 model_unavailable` by default. A separate backend-only loopback research mode can exercise the verified adapter without changing either manifest flag.
This is required because the audit did not establish patient-level
independence, duplicate-leakage absence, or external clinical generalization.

## Preservation and files changed

- Backup created: `backend/.audit_backups/partner_integration_20261025_043700/`.
- Added `backend/app/partner_adapter.py`.
- Updated `backend/app/model_adapter.py` and `backend/app/server.py`.
- Added frontend fields and gated-result rendering in
  `frontend/lib/types.ts`, `frontend/components/analysis/analysis-workspace.tsx`,
  and `frontend/components/results/results-view.tsx`.
- Added the versioned model bundle and `release_manifest.json` under
  `backend/model/artifacts/teammate_partner_v1/`.
- Existing HAM10000/ISIC artifacts, audit archives, source notebooks, and
  existing experiments were not overwritten.

## Artifact integrity

The copied files match the extracted audit package by SHA-256:

| File | SHA-256 |
|---|---|
| `config.json` | `d5ab91d6cac02264a126f318d58d0696972abcdc1ece281fc8647ed7a3e77936` |
| `EffNet-B4.keras` | `4f748c53920fc394b5682442208c4b60116796cf14f4c3e563052d2d6686aa3a` |
| `EffNet-B4-s7.keras` | `28ea3c491a344b62cfb4eaab24e2d874df4fe34f6ff124fec3e6acf4c95cc358` |
| `EffNetV2-S.keras` | `6ed23c6125a35ac171908f91ba479efb7f3e44bcf87de2f5ac336fddaef79f0c` |
| `xgb_tabular.json` | `88ef813e4bc81b36856a53cd6a64aeb4fcc576660d499290136575abc55c1116` |

The pre-existing audit report records a one-character discrepancy for the
`EffNet-B4-s7.keras` hash (`28eac3...`); direct SHA-256 of both the extracted
source and copied file is `28ea3c...`, which is the value used by the release
manifest. The existing audit report was preserved unchanged.

## Adapter contract

The existing endpoint remains `POST /api/cases/{case_id}/analyze` with repeated
multipart `images` and `image_ids` fields. The adapter validates request size,
matching IDs, case ownership, image count, age, supported sex values, and
localization values read from the verified partner configuration. It decodes
JPG/PNG bytes to RGB arrays, preserves multiple-image lesion aggregation, and
returns the partner disclaimer, prediction, risk level, malignancy score,
thresholds, stream scores, and image count without turning the score into
fabricated class probabilities. Inference errors are returned as errors, never
as successful predictions.

The adapter loads TensorFlow/XGBoost lazily only after the release manifest is
approved and all artifact hashes pass. The extracted audit smoke test used
TensorFlow 2.21.0 while the partner requirements declare 2.20.0; this
compatibility remains a documented dependency risk and was not silently
changed in the application environment.

## Evaluation context

The supplied audit recomputed raw image-row accuracy `89.7351%` and AUROC
`0.9334`, separately from lesion-level accuracy `91.7038%` and AUROC
`0.9522`. Neither is represented as clinical validation or as a guarantee of
the 90% target. The package lacks the manifests and patient identifiers
needed to establish patient-level independence and complete duplicate audits.

## Tests and results

- SHA-256 verification of the five copied model artifacts: **passed** against
  the direct hashes of the extracted audit files.
- Python source compilation: **passed** with `py -3.12 -m py_compile`.
- Existing backend safety and partner adapter tests: **passed** (5 tests).
- Frontend TypeScript check: **passed** with `pnpm exec tsc --noEmit`.
- Frontend production build: **passed** with `pnpm build`.
- Running-process smoke test: **passed**; frontend returned HTTP 200, model
  status reported unavailable, and the analysis endpoint returned HTTP 503.
- Real partner checkpoint/API smoke tests: **passed previously in the isolated
  audit environment**; those results are recorded in the teammate audit and
  were not repeated in the serving process because the release gate is off.
- Prior audit evidence (not repeated by this integration change): all three
  CNNs/XGBoost loaded in the isolated audit environment; partner `/info` and
  `/predict` smoke tests passed; current DermaVue status returned unavailable
  and analysis returned 503.
- Final controlled checkpoint smoke: **passed**; three CNNs loaded, one-image
  inference returned the documented research disclaimer, duplicate two-image
  inference preserved `num_images=2` and produced the same lesion score, and
  the authorized image produced BENIGN/LOW/0.0189. This remains software
  verification, not clinical validation.
- Explicit loopback research endpoint smoke: **passed**; the DermaVue endpoint
  returned genuine adapter JSON with `researchMode: true`, while production
  release state remained `serving-disabled`. Invalid sex, localization, and
  non-image input each returned HTTP 400.

## Reproduction commands

From `F:\SkinCancer`:

```powershell
Get-FileHash backend/model/artifacts/teammate_partner_v1/*.keras,backend/model/artifacts/teammate_partner_v1/config.json,backend/model/artifacts/teammate_partner_v1/xgb_tabular.json -Algorithm SHA256
py -3.12 -m py_compile (Get-ChildItem backend/app/*.py | ForEach-Object FullName)
py -3.12 -m unittest backend/test_model_safety.py
Set-Location frontend
pnpm exec tsc --noEmit
pnpm build
```

Do not change both manifest release flags until independent evaluation,
checkpoint compatibility, and an explicit release decision have been
completed. The next integration action is to run the adapter/API tests in the
isolated partner environment, then obtain the missing patient/duplicate
provenance evidence before any serving approval.
