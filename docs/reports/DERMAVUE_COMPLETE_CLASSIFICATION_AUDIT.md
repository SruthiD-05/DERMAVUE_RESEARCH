# DermaVue Complete Classification Audit

## Scope and conclusion

Audited the partner source, configuration, checkpoints, fusion logic, backend adapter/API, and frontend result page. The model is **not a validated multiclass cancer classifier at its final output**. Its release-facing prediction is binary `BENIGN` or `MALIGNANT`, with a lesion-level fused malignancy score and LOW/MODERATE/HIGH thresholds.

The three CNNs internally produce seven-class softmax vectors in the configured order `akiec`, `bcc`, `bkl`, `df`, `mel`, `nv`, `vasc`. The trained stacker does not fuse those seven classes. It receives the malignant aggregate from each CNN (`mel + bcc + akiec`) plus one binary XGBoost score, then emits one fused sigmoid score. Therefore the seven-class values can be exposed only as clearly labelled auxiliary CNN scores; they cannot be presented as the final diagnosis or as validated subtype probabilities.

## Verified model outputs

| Output | Verified meaning | UI treatment |
|---|---|---|
| `prediction` | Final binary threshold decision: `BENIGN` or `MALIGNANT` | Primary result |
| `malignancy_score` | Mean lesion-level fused sigmoid score after multi-image aggregation | Displayed as a model score, not a calibrated probability |
| `risk_level` | Threshold mapping using configured `T_SCR=0.18` and `T_ACC=0.50` | LOW/MODERATE/HIGH styling |
| `screening_flag` | Fused score meets the screening threshold | Preserved in API |
| `stream_scores` | Per-stream malignant aggregate for three CNNs and binary ABCD/metadata XGBoost | Supporting stream details |
| `scores` | Mean of the three CNN seven-class softmax vectors | Displayed as auxiliary CNN class scores, explicitly not final fused subtype output |
| `thresholds` | Partner configuration thresholds | Preserved in API |
| `numImages` | Number of same-lesion images aggregated by arithmetic mean of fused scores | Displayed in input details |

Class score labels are source configuration labels, rendered as Actinic keratosis/intraepidermal carcinoma, Basal cell carcinoma, Benign keratosis-like lesion, Dermatofibroma, Melanoma, Melanocytic nevus, and Vascular lesion.

## Unsupported capabilities

- No final fused seven-class diagnosis exists in the supplied implementation.
- No validated subtype prediction exists for BCC, melanoma, SCC, or any other diagnosis.
- SCC is not one of the seven configured CNN classes.
- The auxiliary CNN scores are not calibrated probabilities and are not used by the final binary stacker as a multiclass distribution.
- The supplied evaluation package does not establish clinical validation, independent patient-level performance, or duplicate-leakage resolution.

## Evidence reviewed

- `backend/model/artifacts/teammate_partner_v1/partner_inference.py`
- `backend/model/artifacts/teammate_partner_v1/config.json`
- `backend/model/artifacts/teammate_partner_v1/release_manifest.json`
- `backend/app/partner_adapter.py`, `backend/app/model_adapter.py`, and `backend/app/server.py`
- `frontend/lib/types.ts`, `frontend/lib/services/index.ts`, and `frontend/components/results/results-view.tsx`
- `docs/reports/TEAMMATE_MODEL_AUDIT.md` and existing integration/readiness reports

## Live research smoke evidence

With explicit loopback research mode enabled and the verified partner artifacts loaded, an authorized HAM10000 image (`ISIC_0024306.jpg`) returned:

- Binary result: `BENIGN`
- Fused malignancy score: `0.0135`
- Auxiliary CNN scores: `akiec 0.0028`, `bcc 0.0013`, `bkl 0.0041`, `df 0.0030`, `mel 0.0145`, `nv 0.9710`, `vasc 0.0032`
- `diagnosisLevel=binary`, `subtypeAvailable=false`, `scoreSource=cnn_auxiliary`
- `researchMode=true`, partner research disclaimer present

This is a software/inference smoke result, not a clinical diagnosis or accuracy evaluation. Production release remains disabled by `evaluation_gate_passed=false` and `serving_enabled=false`.
