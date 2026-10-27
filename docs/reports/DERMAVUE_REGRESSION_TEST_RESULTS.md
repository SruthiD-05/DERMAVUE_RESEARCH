# DermaVue Regression Test Results

## Executed checks

| Check | Result | Evidence |
|---|---|---|
| Backend adapter/safety unit tests | PASS | `py -3 -m unittest backend.test_partner_adapter backend.test_model_safety -v`; 7 tests passed |
| Backend syntax compilation | PASS | `py -3 -m py_compile backend/app/server.py backend/app/partner_adapter.py backend/app/model_adapter.py` |
| Frontend TypeScript check | PASS | `frontend\pnpm exec tsc --noEmit` |
| Frontend production build | PASS | `frontend\pnpm build`; all application routes generated |
| Real API custom case persistence | PASS | Created a unique test case with custom case reference/name; API response and subsequent GET preserved both values and the distinct internal ID |
| Duplicate case reference | PASS | Repeated create returned HTTP 409 with `case_reference_conflict` |
| Real API multi-image storage | PASS | Test case stored 4 images: 2 `dermoscopic`, 2 `clinical`; no modality replacement occurred |
| Real API multi-image inference | PASS | Two dermoscopic files returned HTTP 200 with `numImages=2` and genuine research-model output |
| Invalid metadata | PASS | Invalid sex returned HTTP 400 |
| Frontend automated component tests | NOT AVAILABLE | `frontend/package.json` has no test script or test runner; behavior is implemented in source and validated through build plus real API checks |
| Browser picker interaction | NOT AUTOMATED | No browser automation suite is configured in this project; UI code paths were statically checked and the running frontend remained available on port 3000 |

## Actual multi-image inference response

The live loopback research request used two authorized HAM10000 images and returned:

- HTTP 200
- `numImages=2`
- binary result `BENIGN`
- genuine fused malignancy score `0.3918`
- `diagnosisLevel=binary`
- seven auxiliary CNN scores
- research disclaimer

This is a software smoke result only, not a clinical result or accuracy evaluation.

## Storage cleanup and runtime

The temporary test case and images were removed after validation. The final `backend/data/records.json` contains empty test collections. Frontend and backend listeners remain active on `127.0.0.1:3000` and `127.0.0.1:8000` respectively. Production model serving remains disabled.

## Remaining limitation

Clinical files can now be selected and retained independently, but the current partner model contract intentionally analyzes dermoscopic files only. Clinical images are preserved as context and are not sent to inference unless a future explicitly documented multimodal endpoint supports them.
