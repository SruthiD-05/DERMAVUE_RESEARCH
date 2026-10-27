# Partner API and Analysis UI Requirements Audit

Date: 2026-10-25  
Project: `F:\SkinCancer`  
Release decision: **Serving remains disabled**

## Scope and safety

The audited partner package is preserved under
`incoming/teammate_final_package_audit/backend/backend/`. DermaVue uses the
compatibility adapter in `backend/app/partner_adapter.py`; it does not call the
partner API directly from the browser. The release manifest remains
`evaluation_gate_passed: false` and `serving_enabled: false`. The default live
DermaVue analysis endpoint therefore remains HTTP 503. An explicitly enabled
loopback-only research session is separately allowed to exercise the real
adapter without changing production release state.

## Requirement matrix

| Requirement | Status | Code/evidence |
|---|---|---|
| Partner implements `POST /predict` | PASS | Partner `app.py`, `@app.post("/predict")` |
| Partner accepts multipart `files`, one or more images | PASS | Partner `app.py`; `files: List[UploadFile] = File(...)`; image decode loop |
| Partner accepts JPG/PNG images | PASS | Partner OpenCV decode and 400 unreadable-image error |
| Partner accepts optional numeric `age` | PASS | Partner `age: Optional[float] = Form(None)` |
| Partner restricts `sex` to male/female/unknown | FAIL for direct partner source; PASS at DermaVue adapter boundary | Partner source documents values but does not reject an arbitrary submitted string; DermaVue adapter now rejects unsupported values before loading/inference |
| Partner validates localization against `/info` values | PASS | Partner compares against `model.cfg["LOCS"]`; DermaVue `/api/model/info` now exposes verified `allowedLocalizations` and adapter/server validate against config |
| Partner returns required prediction/risk/score/disclaimer fields | PASS in source and prior isolated smoke test | Partner `inference.py` returns all fields; prior audit verified `/predict` HTTP 200 and documented response |
| DermaVue sends multiple images with matching IDs | PASS in source | `analysisService.run` appends repeated `images` and `image_ids`; backend preserves list order and passes all decoded RGB images to partner model |
| DermaVue forwards age, sex, localization | PASS in source | `analysisService.run`; sex maps unsupported research-record values to partner `unknown` |
| New Case accepts multiple supported dermoscopic images | PASS in source | `new-case-form.tsx`; `multiple` input for dermoscopic uploads and per-image removal |
| Localization options come from verified backend info | PASS in source | `/api/model/info` reads `LOCS` from hash-verified `config.json`; New Case uses `allowedLocalizations` |
| Loading spinner/status and duplicate-submit prevention | PASS in source | `analysis-workspace.tsx`; `running` disables button and shows `Loader2`; request timeout is 120 seconds |
| Startup delay ~30s and inference latency 5–15s tolerated | PASS in source | 120-second analysis timeout; no short client timeout |
| HIGH red / MODERATE amber / LOW green | PASS in source | `results-view.tsx` risk badge classes |
| MODERATE includes dermatologist-review message | PASS in source | `results-view.tsx`: “Recommend dermatologist review.” |
| Score range validation and percentage bar | PASS in source | Backend adapter and frontend validate 0–1; frontend renders `score * 100` only when valid |
| Partner disclaimer always shown on results | PASS in source | Adapter preserves `disclaimer`; frontend renders it and keeps persistent research disclaimer |
| 400/422/503/timeout/network errors are clear | PASS in source; 503 live-tested | `api-client.ts` extracts JSON `message/detail/error`; timeout/network messages; analysis clears stale result; live analysis returned 503 |
| Invalid API responses cannot create a result | PASS in source | `analysisService.run` validates prediction, risk, score, and disclaimer before saving |
| No stale result after failed request | PASS in source | Analysis clears `result` when entering pending and on failure |
| Real partner prediction through DermaVue production serving | NOT TESTABLE | Production release gate remains blocked |
| Real partner prediction through explicit loopback research mode | PASS (software smoke only) | Opt-in backend returned genuine adapter JSON with `researchMode: true`; not clinical validation |

## Verification categories

### Implemented in source

The adapter now decodes uploaded bytes into RGB arrays, validates image count,
sex, localization, score ranges, thresholds, risk/prediction categories, and
the partner disclaimer. The frontend forwards all partner metadata, supports
multiple dermoscopic files, uses verified localization options, validates API
responses, preserves the disclaimer, handles slow requests, and clears stale
results after failure.

### Automated tests executed

- Backend Python compilation: passed.
- Backend safety and partner adapter tests: **5 passed**, including
  release-gate, artifact, metadata, and invalid-image checks.
- Frontend TypeScript check: passed after the focused changes.
- Frontend production build: passed after the focused changes.

No separate frontend unit-test framework exists in the current project, so
rendering requirements are verified by source inspection and production build;
mocked predictions were not presented as real inference.

### Actual model/API evidence

The earlier isolated audit loaded all three CNN checkpoints and XGBoost, and
verified the partner FastAPI `/info` and `/predict` smoke paths using an
authorized public HAM10000 image. One-image and duplicate two-image inference
succeeded, with duplicate lesion scores equal. That was a software smoke test,
not clinical validation. The current DermaVue process was not allowed to load
or serve the model because the release gate is disabled.

### Release-gate blockers

Patient-level independence, duplicate/source overlap, confidence intervals,
and complete frozen split provenance remain unresolved. The partner source's
direct API also needs explicit `sex` rejection if it is ever deployed
standalone; the DermaVue adapter boundary already enforces that contract.

## Safe runtime checks

With the existing services running:

- DermaVue `/api/model/info`: HTTP 200; returns partner name/version,
  three-CNN + ABCD/metadata architecture, verified localization values, and
  labelled unverified research metrics.
- Default DermaVue `/api/model/status`: HTTP 200; reports installed artifacts,
  not-loaded checkpoint, serving-disabled release, and inference unavailable.
- Default DermaVue `/api/cases/{case_id}/analyze`: HTTP 503 `model_unavailable`.
- Explicit loopback research mode: status reports `research-available` and the
  same endpoint reaches the real adapter; production `releaseState` stays
  `serving-disabled`.
- Frontend routes `/dashboard`, `/cases`, `/patients`, `/model`, and
  `/cases/new`: HTTP 200.

No release flag, checkpoint, research artifact, or frontend architecture was
overwritten. No synthetic prediction was used as evidence.
