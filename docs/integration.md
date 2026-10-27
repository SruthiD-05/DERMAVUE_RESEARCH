# DermaVue integration notes

## Endpoints

- `GET /health` and `GET /api/health`: service health and model status summary.
- `GET /api/model/status`: backend/checkpoint/inference availability.
- `GET /api/model/info`: source-reported architecture and limitations.
- `GET/POST /api/patients`, `GET/PATCH/DELETE /api/patients/{id}`: patient records.
- `GET/POST /api/cases`, `GET/PATCH/DELETE /api/cases/{id}`: case records.
- `GET/POST /api/cases/{id}/images`: image records sent by the remote-data frontend mode.
- `POST /api/cases/{case_id}/analyze`: currently returns `503 model_unavailable` because no V2 checkpoint is supplied.
- `POST /api/reports/{case_id}/export`: returns an honest unavailable response until a model result exists.

## Data handling

In the default local mode, patient, case, and image records remain in the browser's
IndexedDB. If `NEXT_PUBLIC_DERMAVUE_DATA_MODE=remote` is explicitly selected, the
backend persists those records in `backend/data/records.json`; this is a simple
local research store, not a production medical-records service. The model adapter
still refuses inference because the available experiment checkpoint is synthetic
and incompatible with the V2 five-category serving contract.

To use remote CRUD mode, set:

```powershell
$env:NEXT_PUBLIC_DERMAVUE_API_URL = 'http://127.0.0.1:8000'
$env:NEXT_PUBLIC_DERMAVUE_DATA_MODE = 'remote'
```

For the local frontend dev server, the non-secret backend URL is also supported
through `frontend/.env.local`:

```text
NEXT_PUBLIC_DERMAVUE_API_URL=http://127.0.0.1:8000
```

Restart the frontend after changing this file. This configures connectivity
only; it does not approve a checkpoint or enable analysis.
