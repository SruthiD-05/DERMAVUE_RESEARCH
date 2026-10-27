# Portable Package Validation

Package: `DermaVue_Research_Package.zip`

Package date: 2026-10-25

## Included

Frontend source and lockfile, Python backend, exact partner model checkpoints and configuration, tests, setup/start/stop PowerShell scripts, integration reports, research documentation, and `.env.example`.

## Deliberately omitted

HAM10000/ISIC image datasets, virtual environments, `node_modules`, Next build output, caches, logs, notebooks, temporary files, and unrelated generated experiment outputs. These are not required to start the application and may have separate licensing or redistribution restrictions.

## Model inventory

The included bundle is `backend/model/artifacts/teammate_partner_v1/`:

- `EffNet-B4.keras`
- `EffNetV2-S.keras`
- `EffNet-B4-s7.keras`
- `xgb_tabular.json`
- `config.json`
- `partner_inference.py`
- `release_manifest.json`

The manifest contains the expected SHA-256 values. The package was copied from the audited workspace without modifying weights or score semantics. The bundle is a research artifact; no clinical redistribution or diagnostic approval is asserted.

Verified SHA-256 values in the staged copy:

| File | SHA-256 |
|---|---|
| `config.json` | `d5ab91d6cac02264a126f318d58d0696972abcdc1ece281fc8647ed7a3e77936` |
| `EffNet-B4.keras` | `4f748c53920fc394b5682442208c4b60116796cf14f4c3e563052d2d6686aa3a` |
| `EffNet-B4-s7.keras` | `28ea3c491a344b62cfb4eaab24e2d874df4fe34f6ff124fec3e6acf4c95cc358` |
| `EffNetV2-S.keras` | `6ed23c6125a35ac171908f91ba479efb7f3e44bcf87de2f5ac336fddaef79f0c` |
| `xgb_tabular.json` | `88ef813e4bc81b36856a53cd6a64aeb4fcc576660d499290136575abc55c1116` |

## Tests executed before packaging

- Backend adapter and safety tests: 7 passed.
- Python compilation of active backend modules: passed.
- Frontend TypeScript check: passed.
- Frontend production build: passed.
- Real loopback research inference: HTTP 200 with binary output, seven auxiliary scores, disclaimer, and dynamic top-score data.

## Extracted-copy validation on the packaging laptop

- ZIP opened and extracted: passed; 213 entries.
- Required source, scripts, documentation, and model files: present.
- All five manifest-listed model hashes in the extracted copy: matched.
- Backend tests from the extracted copy: 7 passed.
- Frontend dependency install with the frozen lockfile: passed.
- Extracted frontend TypeScript check: passed.
- Extracted frontend production build: passed.
- Extracted backend health on `127.0.0.1:8001`: HTTP 200.
- Extracted frontend development server on `127.0.0.1:3001`: HTTP 200.
- Extracted model loading and real inference: not completed because the packaging laptop's current Python environment lacks `xgboost`; no model dependency installation was performed into the user's existing environment. Run `scripts\setup_windows.ps1` in the package's clean `.venv` before attempting inference.

The extracted package must still be validated on the recipient's laptop after dependency installation. TensorFlow model loading is hardware- and dependency-sensitive. The release gate remains `evaluation_gate_passed=false` and `serving_enabled=false`.

## Recipient startup

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
.\scripts\start_all.ps1
Invoke-WebRequest http://127.0.0.1:8000/health
Start-Process http://127.0.0.1:3000
```

Use `scripts\stop_all.ps1` to stop only processes recorded by the package. Use authorized research images only. Do not treat results as medical diagnoses or as independent clinical validation.
