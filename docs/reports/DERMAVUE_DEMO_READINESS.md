# DermaVue Demo Readiness

Date: 2026-10-25  
Status: **Software demo-ready with analysis intentionally unavailable**

The verified current status is **Model installed — serving disabled**. The
frontend is connected to the backend, the partner artifact hashes are valid,
and the release manifest remains explicitly unapproved and non-serving.

## Analysis-button root cause

Clicking Run model analysis currently follows this path: the frontend first
requests `GET /api/model/status`; because `inferenceAvailable` is false, it
marks the case unavailable and stops before building or sending the multipart
analysis request. The UI now explains that release approval is pending and
that the uploaded images were not rejected. A direct safe `POST
/api/cases/existing-case/analyze` check returns HTTP 503 with
`error: model_unavailable`; the backend rejects before image parsing or model
inference. This is a release decision, not an image or metadata validation
failure.

## Release decision

The partner model remains behind the existing safety gate. The release
manifest at `backend/model/artifacts/teammate_partner_v1/release_manifest.json`
has `evaluation_gate_passed: false` and `serving_enabled: false`.
Therefore `/api/cases/{case_id}/analyze` must continue returning
`503 model_unavailable`. No fabricated or cached prediction is displayed.

The backend status distinguishes configuration, artifact integrity, load
state, and release state. It reports `artifactState: installed`,
`loadState: not-loaded`, `releaseState: serving-disabled`,
`checkpointLoaded: false`, and `inferenceAvailable: false`. The model name,
version, architecture, and metrics come from the hash-verified partner
manifest/configuration rather than the old generic V2 fallback. Metrics are
labelled unverified research-package results.

An explicit loopback-only research mode is available through the backend
variable `DERMAVUE_RESEARCH_INFERENCE_ENABLED=true`. It does not modify the
release manifest or production serving state. The current verification session
loaded the real bundle and exercised the DermaVue analysis endpoint with an
authorized research image; the response carried `researchMode: true` and the
partner disclaimer.

This is a software-readiness decision, not clinical validation. The supplied
evaluation package still lacks patient-level independence evidence, a complete
duplicate-leakage audit, confidence intervals, and independently reconstructible
split manifests.

## Model and dependency verification

- The five isolated checkpoint/configuration hashes match the direct extracted
  audit artifacts and the integration manifest.
- The isolated audit environment uses Python 3.12.4, TensorFlow 2.21.0,
  XGBoost 3.4.1, OpenCV 5.0.0, and FastAPI 0.135.3.
- The partner package declares TensorFlow 2.20.0. Compatibility was checked in
  the isolated environment; the existing project dependencies were not changed.
- Actual loading smoke test succeeded for all three CNNs and XGBoost.
- Authorized image: `data/processed/ham10000/images_part_1/ISIC_0024306.jpg`.
- One-image inference returned `BENIGN`, `LOW`, malignancy score `0.0189`,
  screening flag `false`, and the documented research disclaimer.
- Duplicate two-image inference returned `num_images=2` and the same lesion
  score, confirming the documented averaging path for identical inputs.
- Invalid image bytes failed with a decode error. This confirms software
  rejection, not clinical safety.

## Evaluation evidence

The earlier audit independently reproduced the supplied result files:

- Raw image-score result: **89.7351% accuracy**, **0.9334 AUROC**.
- Lesion-level result: **91.7038% accuracy**, **0.9522 AUROC**.
- The reported 89.34% image-row result is based on lesion-average scores
  broadcast to image rows, not an independent raw image-score prediction.

These are research-package results only. They do not establish patient-level
independence, external generalization, or clinical performance.

## Frontend verification

The existing architecture and design were preserved. Verified routes returned
HTTP 200 while the dev server remained running at `http://127.0.0.1:3000`:
`/`, `/dashboard`, `/patients`, `/cases`, `/model`, `/reports`, and `/about`.

The analysis and results views retain the research disclaimer, show the gated
unavailable state, and render partner risk styling and malignancy score only
when those fields are returned by a genuine model response. No direct partner
API call was added to the frontend.

## End-to-end smoke test

A temporary patient, linked case, and permitted test-image record were created
through the running backend, navigated successfully, and deleted afterward.
The case read returned HTTP 200. The analysis request returned HTTP 503, and
the records were confirmed absent after cleanup.

Running service checks:

- Backend health: HTTP 200 / `status: ok`.
- Model status: HTTP 200 / `inferenceAvailable: false`.
- Analysis endpoint: HTTP 503 / `model_unavailable`.
- Frontend: HTTP 200 at `127.0.0.1:3000`.

## Tests executed

- `py -3.12 -m py_compile` for backend application modules: passed.
- `py -3.12 -m unittest backend/test_model_safety.py backend/test_partner_adapter.py`: **6 passed**.
- `pnpm exec tsc --noEmit`: passed.
- `pnpm build`: passed.
- Actual isolated partner model loading/inference smoke test: passed.
- One-image, duplicate multi-image, and invalid-image smoke paths: passed.
- CRUD/navigation/unavailable-model smoke: passed; temporary records cleaned.
- Health, model-status, analysis, and frontend route checks: passed as recorded above.
- Final controlled partner checkpoint smoke: passed; three CNNs loaded, one
  image returned BENIGN/LOW/0.0189 with the partner disclaimer, and duplicate
  two-image inference preserved the same lesion-level score.
- Explicit loopback research endpoint smoke: passed; one-image and two-image
  requests returned genuine adapter JSON with `researchMode: true`; invalid
  sex, localization, and image inputs returned HTTP 400. Production serving
  remains disabled.
- Model status correction smoke: passed; `/api/model/status` reports the
  partner tri-modal name/version/architecture, installed artifact state, and
  serving-disabled release state; `/api/model/info` reports the same verified
  partner configuration and labelled metrics.

The unavailable-gate state prevented live DermaVue adapter inference, invalid
multipart analysis, timeout, and model-loading-failure requests from reaching
the partner adapter. Those cases remain covered by the adapter's validation
and release gate, but are not claimed as live endpoint passes.

## Known issues and next approval requirements

Before enabling analysis, obtain and review patient identifiers, complete
duplicate/source overlap audits, preserve frozen train/validation/test
manifests, resolve the TensorFlow 2.20/2.21 deployment choice, and document a
separate release decision. Do not change both release flags merely for a demo.

Confirmed release blockers are the missing patient-level independence
evidence, unresolved duplicate/source overlap audit, missing frozen split
provenance/manifests, absent confidence intervals, and the unresolved
TensorFlow 2.20 versus 2.21 deployment choice. The controlled checkpoint
smoke test only establishes that the software can load and run; it does not
clear any of these blockers or establish clinical validation.

## Startup commands

Backend:

```powershell
py -3.12 -m backend.app.server
```

Frontend:

```powershell
Set-Location frontend
pnpm dev --hostname 127.0.0.1
```

## Demo walkthrough

1. Open `http://127.0.0.1:3000`.
2. Show patient and case navigation, image preview, and the analysis workspace.
3. Select a case with a dermoscopic image and open Analysis.
4. Show the persistent research disclaimer and the honest unavailable-model
   status; the run button remains disabled while the release is blocked.
5. Use the Model page to show the backend status and explain that no clinical
   prediction is being presented until independent release review is complete.
