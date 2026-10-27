# DermaVue MobileNetV2 Experiment Report

Date: 2026-09-28  
Project: `F:\SkinCancer`

## Executive result

No valid clinical melanoma experiment reached 95% accuracy. The only executable dataset bundled with the teammate’s V2 archive is a deliberately synthetic demo set. On that set, both the original V2 fusion pipeline and the frozen-ImageNet-MobileNetV2 variant scored 100% on the same 90-image held-out demo split. Those numbers are software-validation results only and must not be interpreted as melanoma detection performance.

V1 was not found in the project, backup, or supplied ZIP. The backup contains a separate MILK10k multimodal research pipeline, not a V1 implementation of this teammate model. V1 rows are therefore unavailable rather than recreated or inferred.

## Source and architecture audit

The supplied V2 source is preserved under `backend/model/v2_source` and was copied unchanged into the experiment directories. V2 is a hybrid pipeline:

1. Image preprocessing performs resizing, denoising/hair removal, and normalization.
2. Otsu thresholding and morphology produce a lesion mask.
3. The original CNN branch uses three Conv2D/BatchNorm/ReLU/MaxPool blocks, global average pooling, a 64-unit `deep_features` projection, dropout, and a binary sigmoid head.
4. The handcrafted branch extracts ABCD-style asymmetry, border/compactness, colour statistics, diameter, and GLCM texture features.
5. The deep and handcrafted vectors are standardized and fused.
6. SVM-RBF, Random Forest, and XGBoost classifiers are compared; the original script selects by AUC.

The MobileNetV2 experiment replaces only the original CNN branch with `tf.keras.applications.MobileNetV2(include_top=False, pooling="avg", weights="imagenet")`, freezes the backbone, applies MobileNetV2 preprocessing, and retains the same 64-unit feature projection, handcrafted branch, fusion scaler, and classical classifiers. The classifier remains binary for the bundled synthetic demo labels: `0=benign`, `1=melanoma`.

The source also contains a separate HAM10000-oriented five-category pipeline (`train_real.py`) with lesion-level splitting, metadata processing, skin-tone proxy evaluation, and an optional MobileNetV2 branch. No compatible HAM10000 image/metadata contract or trained checkpoint was supplied with the V2 archive, so that pipeline was not represented as a completed result here.

## Dataset inventory and provenance

| Item | Finding |
|---|---|
| V2 archive | `C:\Users\fahad\Downloads\melanoma_hybrid_v2.zip`; source, README, synthetic data, and precomputed demo outputs; no checkpoint or serving API |
| V2 executable data | 360 synthetic JPGs: 180 benign and 180 melanoma, arranged by synthetic light/medium/dark tone folders |
| Experiment split | Same V2 script split for both runs: 229 train, 41 validation, 90 test; test contains 45 images per class |
| Genuine data available elsewhere | Backup contains MILK10k/ISIC-derived data and lesion-level splits, but it belongs to a different multimodal codebase and label contract; it was not substituted into V2 |
| V1 | Not located; no V1 result was fabricated |

The synthetic generator intentionally makes classes separable by shape/colour/ABCD characteristics. Its results are not evidence of real-world sensitivity, specificity, or clinical utility. Patient/lesion leakage checks cannot convert this synthetic dataset into a clinical benchmark.

## Actual experiment results

The following are metrics obtained by rerunning the scripts, not copied from the archive summary. Metrics are on the synthetic held-out demo split only.

| Version | Architecture | Accuracy | Macro F1 | Sensitivity | Specificity | Test samples |
|---|---|---:|---:|---:|---:|---:|
| V1 baseline | Unavailable | N/A | N/A | N/A | N/A | N/A |
| V1 improved | Unavailable | N/A | N/A | N/A | N/A | N/A |
| V2 baseline | Original CNN + ABCD/texture + classical fusion (SVM) | 1.000 | 1.000 | 1.000 | 1.000 | 90 synthetic |
| V2 improved | Frozen ImageNet MobileNetV2 + same fusion (SVM) | 1.000 | 1.000 | 1.000 | 1.000 | 90 synthetic |

For V2, Random Forest and XGBoost also obtained 1.000 for all listed metrics. ROC-AUC was 1.000 for the fused classifiers. The CNN-only ablation was 0.500 accuracy for the original branch and 1.000 for MobileNetV2. This difference is a demo-pipeline observation, not a claim about real melanoma performance.

No genuine held-out test-set comparison between V1 and V2, or between original and MobileNetV2 models, is available. Therefore no clinically meaningful winner can be selected.

## Reproducible artifacts

- Original V2 experiment: `experiments/v2_original_baseline/`
- MobileNetV2 experiment: `experiments/v2_mobilenetv2/`
- MobileNetV2 checkpoint: `experiments/v2_mobilenetv2/outputs/cnn_branch.keras`
- MobileNetV2 fusion scaler/classifier: `experiments/v2_mobilenetv2/outputs/fusion_classifier.joblib`
- Configuration and class mapping: `experiments/v2_mobilenetv2/outputs/experiment_config.json`
- Metrics: `experiments/v2_mobilenetv2/outputs/results_summary.csv`
- Training log: `experiments/v2_mobilenetv2/train.log`
- Inference smoke script: `experiments/v2_mobilenetv2/inference.py`

The original baseline has the corresponding files under `experiments/v2_original_baseline/outputs/`. The saved MobileNetV2 model uses ImageNet weights downloaded by Keras and a frozen backbone. Package versions used were TensorFlow 2.21.0, scikit-learn 1.9.1, OpenCV 5.0.0, scikit-image 0.26.0, XGBoost 3.4.1, pandas 3.0.2, and Python 3.12.4. TensorFlow ran CPU-only on native Windows; the installed RTX 4050 was not used by native TensorFlow.

Training and inference wall-clock timing was not instrumented by the original scripts, so no invented timing numbers are reported.

## Verification performed

- Python bytecode compilation: passed for backend and both experiment source trees.
- V2 original training/evaluation: passed on the 360-image synthetic demo.
- V2 MobileNetV2 training/evaluation: passed on the identical split.
- Saved MobileNetV2 model loading/inference: passed on a compatible synthetic image; output mapping was `benign` with a numeric melanoma probability.
- Corrupted/unsupported real-image inference: not claimed; no genuine compatible unseen image was available.
- Backend smoke test: `/api/health` returned 200, model status reported unavailable, and `/api/cases/test/analyze` returned the expected 503 safety response.
- Frontend TypeScript check: passed.
- Frontend production build: passed with Next.js 16.3.3.
- Backend unit-test discovery: executed; no backend tests were present (`0 tests ran`).

The current backend adapter and frontend were not changed. This is intentional: the experiment checkpoint is a synthetic-demo artifact and is not a verified production model. The existing model-unavailable behavior remains active.

## Exact reproduction commands

From `F:\SkinCancer` using `C:\Users\fahad\AppData\Local\Programs\Python\Python312\python.exe`:

```powershell
python -m pip install tensorflow-cpu scikit-learn xgboost opencv-python scikit-image openpyxl

Push-Location experiments\v2_original_baseline\src
python train.py --data_dir ..\data\synthetic_dataset --out_dir ..\outputs --epochs 5
Pop-Location

Push-Location experiments\v2_mobilenetv2\src
python train.py --data_dir ..\data\synthetic_dataset --out_dir ..\outputs --epochs 5
Pop-Location

python experiments\v2_mobilenetv2\inference.py `
  experiments\v2_mobilenetv2\outputs\cnn_branch.keras `
  experiments\v2_mobilenetv2\data\synthetic_dataset\benign\light\benign_light_000.jpg

python -m compileall -q backend experiments\v2_original_baseline\src experiments\v2_mobilenetv2\src
```

## Limitations and required next inputs

Before any real comparison or DermaVue integration, the project needs the actual V1 source, a compatible genuine labeled dataset with documented provenance, patient/lesion identifiers, fixed train/validation/test manifests, and verified checkpoints or enough compute time to train them. The final model must be evaluated on an untouched lesion-level test set with per-class precision/recall, balanced accuracy, macro F1, ROC-AUC where applicable, confusion matrix, and timing. The current synthetic checkpoints must not be connected to the backend or described as clinically validated.
