# Local Research Inference

Status: **Opt-in local research mode; production/general serving remains disabled**

## Safety boundary

Local research inference is controlled by the backend-only environment variable:

```powershell
$env:DERMAVUE_RESEARCH_INFERENCE_ENABLED = 'true'
py -3.12 -m backend.app.server
```

The default is effectively `false` when the variable is absent. The frontend
cannot activate this mode. The backend refuses to start research mode on a
non-loopback host and the normal release manifest remains unchanged:

```json
"evaluation_gate_passed": false,
"serving_enabled": false
```

Research mode requires the hash-verified bundle under
`backend/model/artifacts/teammate_partner_v1/`. It loads the real three-CNN
and XGBoost pipeline, never synthetic predictions, and reports
`researchMode: true` separately from production serving.

## Local startup

Start the backend only on loopback:

```powershell
Set-Location F:\SkinCancer
$env:DERMAVUE_RESEARCH_INFERENCE_ENABLED = 'true'
py -3.12 -m backend.app.server
```

Keep the frontend pointed at `http://127.0.0.1:8000` through
`frontend/.env.local`. The existing frontend request uses the DermaVue
endpoint and sends repeated `images`/`image_ids` fields plus age, sex, and
verified localization. The adapter decodes the images and preserves the
partner's multi-image lesion aggregation.

When the frontend uses browser-local case storage, an explicitly enabled
loopback research request may use an ephemeral case ID; uploaded bytes and
metadata are validated and inferred without copying the local patient/case
record into the backend store. Remote-data mode continues to require a
server-side case and image ownership match.

Do not bind this process to `0.0.0.0`, expose it to another device, or use it
for patient care. Additional authentication and network controls would be
required for any non-loopback deployment.

## Verified behavior

- Default-disabled backend: `release-disabled`, `checkpointLoaded=false`,
  `inferenceAvailable=false`, and analysis HTTP 503.
- Opt-in backend: loads the hash-verified partner bundle before serving and
  reports `research-available`, `researchMode=true`, production
  `releaseState=serving-disabled`, and `inferenceAvailable=true`.
- The controlled authorized HAM10000 smoke image
  `data/processed/ham10000/images_part_1/ISIC_0024306.jpg` loaded all three
  CNNs and XGBoost. With `TTA_VIEWS=2` for a CPU smoke test, it returned
  BENIGN/LOW with malignancy score `0.0189` and the partner disclaimer.
  Duplicate two-image input returned the same lesion score.
- A live DermaVue endpoint request using an ephemeral local-research case ID
  reached the real adapter and returned `researchMode: true`, BENIGN/LOW,
  malignancy score `0.0135`, and the partner disclaimer; no temporary record
  was persisted. A duplicate two-image request returned `numImages=2` and the
  same `0.0135` lesion score.

These are software smoke outputs, not diagnoses, accuracy claims, clinical
validation, or release approval. The existing research limitations remain:
patient-level independence, duplicate/source overlap, frozen split provenance,
confidence intervals, and deployment-version review are unresolved.

## Reproduce checks

```powershell
Get-FileHash backend/model/artifacts/teammate_partner_v1/* -Algorithm SHA256
py -3.12 -m unittest backend/test_model_safety.py backend/test_partner_adapter.py
Set-Location frontend
pnpm exec tsc --noEmit
pnpm build
```
