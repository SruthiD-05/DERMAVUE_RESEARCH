# DermaVue Research Package

Portable Windows package for the DermaVue local research application. It includes the frontend, backend, the hash-verified partner model bundle, integration code, tests, and research documentation.

## Important research limitation

This is not a clinical diagnostic system. The partner model's final output is binary (`BENIGN`/`MALIGNANT`); the seven auxiliary CNN scores are not calibrated probabilities or confirmed subtype diagnoses. The release manifest intentionally remains `evaluation_gate_passed=false` and `serving_enabled=false`. The startup scripts enable only loopback research inference when the scientific dependencies and checkpoints load successfully.

## Prerequisites

- Windows 10/11
- Python 3.12 (recommended; 3.10+ may work)
- Node.js 20.9+ and pnpm 12+
- At least 8 GB free disk space and sufficient RAM for TensorFlow model loading
- Network access for first-time dependency installation

## One-time setup

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
```

The script creates `.venv`, installs the backend scientific dependencies required by the included partner bundle, installs frontend dependencies from the lockfile, and creates `frontend\.env.local` from `.env.example` if it is missing. It does not download datasets or copy personal configuration.

## Start and stop

```powershell
.\scripts\start_all.ps1
.\scripts\stop_all.ps1
```

Alternatively use `start_backend.ps1` and `start_frontend.ps1` in separate PowerShell windows.

- Frontend: http://127.0.0.1:3000
- Backend health: http://127.0.0.1:8000/health
- Model status: http://127.0.0.1:8000/api/model/status
- Model contract: http://127.0.0.1:8000/api/model/info

The first backend start may take approximately 30 seconds while TensorFlow loads the three checkpoints. The frontend stores patients and cases in browser IndexedDB. Create a patient and case, upload one or more supported JPG/PNG images, and run analysis only for authorized research images.

## Troubleshooting

- If Python is not found, install Python 3.12 and ensure `py` or `python` is on PATH.
- If TensorFlow or XGBoost installation fails, confirm a supported 64-bit Python version and rerun setup.
- If model status reports artifacts invalid, compare the included hashes with `backend\model\artifacts\teammate_partner_v1\release_manifest.json`.
- If port 3000 or 8000 is busy, stop the owning application or use a separately configured local port; do not terminate unrelated processes.
- If the frontend says the backend is unavailable, confirm `NEXT_PUBLIC_DERMAVUE_API_URL` in `frontend\.env.local`.

## Omitted data

Large HAM10000/ISIC datasets, temporary environments, caches, notebooks, generated logs, and unrelated experiment outputs are intentionally omitted. Obtain datasets only from official sources and comply with their licences. The included model bundle is the partner-supplied research artifact; its provenance and limitations are documented in `docs\reports\TEAMMATE_FINAL_PACKAGE_AUDIT.md` and `docs\PORTABLE_PACKAGE_VALIDATION.md`.
"# DERMAVUE_RESEARCH" 
