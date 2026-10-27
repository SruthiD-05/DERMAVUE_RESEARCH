# DermaVue Multi-Image and Case-ID Fix

## Root causes

### Multi-image replacement

`frontend/components/patients/new-case-form.tsx` previously removed every existing image of the selected modality before adding new files:

```ts
[...x.filter((i) => i.kind !== kind), ...items]
```

Clinical selection also used `find()` and limited the input to one file. This caused repeated picker operations to replace selections and prevented multiple clinical photographs.

### Case identity display

The frontend generated an internal `case.id` and sent it to the backend, but the case list, details, results, reports, and patient case list rendered that internal value instead of a separate user-facing case label. There were no persisted case ID/name fields.

## Changes

- Added persisted optional `caseReference` and `caseName` fields to the case contract.
- Kept generated `id` as the stable internal identifier.
- Added case ID/name inputs and review summary to New Case.
- Added `caseDisplayLabel()` and updated case list, case detail, results, reports, and patient views.
- Added backend `409` conflict responses for duplicate case references/names on create and update.
- Preserved entered values in API responses and storage; blank fields fall back to lesion ID, then internal ID for display.
- Changed both modality selectors to append across picker operations and support multiple files.
- Added a documented maximum of four files per modality, matching the model adapter’s maximum supported analysis input count for dermoscopic images.
- Added SHA-256 file identity checks to reject duplicate bytes, MIME/size validation, image decode validation, per-image removal, per-modality Clear all, modality labels, and file-input reset.
- Preserved clinical and dermoscopic kinds independently. Only dermoscopic images are sent to the current model analysis contract; clinical images remain case context.

## API and persistence behavior

The backend continues to receive repeated `images` and `image_ids` multipart fields for dermoscopic analysis. The adapter preserves lesion-level aggregation and returns the actual analyzed image count. Clinical images remain stored with `kind=clinical` and are not silently mixed into model inference.

The JSON store now persists `caseReference` and `caseName` alongside the internal `id`. Existing records without these fields remain compatible.

## Safeguards preserved

- No model weights, fusion logic, score semantics, or thresholds changed.
- `evaluation_gate_passed=false` and `serving_enabled=false` remain unchanged.
- Frontend remains on port 3000; backend remains loopback-only on port 8000 in explicit research mode.
- Existing records were preserved. The only removed row was the test-only patient accidentally created during API validation, identified by `reference=E2E research subject`; final backend storage contains empty test collections.
