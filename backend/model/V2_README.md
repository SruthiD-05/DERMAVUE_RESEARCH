# Hybrid CNN + Classical-ML Melanoma Detection

Implementation of the hybrid architecture proposed in the literature survey
("AI-Based Early Detection of Skin Cancer Using Image Analysis in High UV
Exposure Regions"), designed to directly test the research gap identified
there: **most published models report only aggregate accuracy and are
trained on datasets (ISIC, HAM10000) that underrepresent darker skin
tones.** This project's evaluation step reports accuracy *per skin-tone
group*, not just in aggregate, by design.

## Architecture

```
                 ┌────────────────────┐
   lesion image →│  Preprocessing     │  hair removal (blackhat + inpaint),
                 │  (preprocessing.py)│  resize, normalize
                 └─────────┬──────────┘
                           ▼
                 ┌────────────────────┐
                 │  Segmentation      │  Otsu threshold + morphology
                 │  (segmentation.py) │  → lesion mask
                 └─────────┬──────────┘
              ┌────────────┴────────────┐
              ▼                         ▼
   ┌─────────────────────┐   ┌───────────────────────────┐
   │  CNN branch          │   │  Handcrafted ABCD branch   │
   │  (cnn_model.py)       │   │  (handcrafted_features.py) │
   │  Conv-BN-ReLU x3 →     │   │  Asymmetry, Border          │
   │  GAP → Dense(64)       │   │  compactness, Color std,    │
   │  = deep feature vector │   │  Diameter, GLCM texture     │
   └───────────┬───────────┘   └─────────────┬───────────────┘
               └────────────┬────────────────┘
                            ▼
                 ┌────────────────────────┐
                 │  Feature fusion         │  concatenate + StandardScaler
                 │  (fusion_classifier.py) │
                 └───────────┬─────────────┘
                             ▼
                 ┌────────────────────────┐
                 │  Classical classifier   │  SVM / RandomForest / XGBoost
                 │  (fusion_classifier.py) │  (compared; best by AUC reported)
                 └───────────┬─────────────┘
                             ▼
                 ┌────────────────────────┐
                 │  Evaluation             │  overall metrics AND
                 │  (evaluate.py)          │  metrics broken out per
                 │                         │  skin-tone group
                 └────────────────────────┘
```

This is a genuine hybrid model (matching the "Kawahara et al." hybrid
approach discussed in the survey's literature review): the CNN is not the
final classifier. It's a learned feature extractor, whose output is fused
with clinically-grounded handcrafted features before a classical ML model
makes the final call.

## Files

| File | Purpose |
|---|---|
| `data/generate_synthetic_data.py` | Creates a synthetic demo dataset (NOT real medical data) to validate the pipeline runs correctly end-to-end |
| `src/preprocessing.py` | Hair removal, denoising, resizing |
| `src/segmentation.py` | Otsu-based lesion segmentation |
| `src/handcrafted_features.py` | ABCD rule + GLCM texture features |
| `src/cnn_model.py` | Lightweight CNN branch (trained from scratch) + feature extractor |
| `src/fusion_classifier.py` | Feature fusion + SVM/RandomForest/XGBoost classifiers |
| `src/dataset.py` | Loads `class/skin_tone/*.jpg` folder structure |
| `src/evaluate.py` | Overall + skin-tone-stratified metrics, fairness gap |
| `src/train.py` | Runs the full pipeline end to end |

## Running it (synthetic demo data, already generated)

```bash
cd src
python train.py --data_dir ../data/synthetic_dataset --out_dir ../outputs --epochs 15
```

Outputs: `outputs/results_summary.csv` (model comparison),
`outputs/results_by_skin_tone.xlsx` (per-tone breakdown per classifier).

**Note on the demo results:** on the synthetic data, the fused hybrid
model reaches ~100% accuracy. This is expected and NOT a real-world
performance claim — the synthetic benign/melanoma shapes were generated
with clearly separable ABCD characteristics (regular vs. irregular
border, single vs. multi-color) specifically so the pipeline's mechanics
could be verified quickly without a GPU or external dataset access. Real
accuracy must come from training on real dermoscopic images (below).

## Using real data (HAM10000) -- 3-branch, 5-class pipeline

This sandbox cannot reach Kaggle/Drive, so this step runs in Colab or on
your own machine, where you've already downloaded HAM10000 (via
`kaggle datasets download -d kmader/skin-cancer-mnist-ham10000`) and
mounted Drive.

This is a **separate, more ambitious pipeline** from the binary
synthetic-data demo above: 3 fused branches (CNN image + ABCD handcrafted
+ patient metadata) classifying into **5 risk categories** instead of a
binary benign/melanoma call:

| `dx` code(s) | Risk category |
|---|---|
| `nv` | Normal Skin |
| `bkl`, `df` | Skin Allergy/Acne |
| `vasc`, `akiec` | Suspicious Lesion |
| `bcc` | Possible Skin Cancer (Basal Cell Carcinoma) |
| `mel` | Possible Skin Cancer (Melanoma) |

New files for this pipeline (synthetic-data files above are untouched):

| File | Purpose |
|---|---|
| `src/metadata_features.py` | 3rd branch: age/sex/localization → feature vector; also defines the 5-class mapping above |
| `src/skin_tone_proxy.py` | HAM10000 has **no** skin-tone/Fitzpatrick labels, so this estimates one (ITA angle from perilesional skin) to preserve the stratified-fairness evaluation on real data. **Documented proxy, not ground truth** -- say so in any write-up. |
| `src/real_dataset.py` | Loads real HAM10000 images by `image_id` across the two image-part folders; caps images per class so a CPU-only Colab run stays tractable |
| `src/train_real.py` | Orchestrates the full 3-branch, 5-class run |

`cnn_model.py`, `fusion_classifier.py`, `evaluate.py` each gained
multiclass-capable additions (`build_cnn_multiclass`, `fuse_three_branches`,
`build_classifiers_multiclass`, `evaluate_overall_and_stratified_multiclass`,
`per_class_report`, ...) alongside their original binary versions, which
`train.py` still uses unchanged.

Run (from `src/`):
```bash
python train_real.py \
  --metadata_csv "/content/drive/MyDrive/skin cancer inhouse project/Skin Cancer/ham10000_data/HAM10000_metadata.csv" \
  --images_dir   "/content/drive/MyDrive/skin cancer inhouse project/Skin Cancer/ham10000_data/ham10000_images_part_1" \
  --images_dir   "/content/drive/MyDrive/skin cancer inhouse project/Skin Cancer/ham10000_data/ham10000_images_part_2" \
  --out_dir ../outputs_real --max_per_class 250 --epochs 20
```

**Runtime / class imbalance:** the raw data is 6705 `nv` vs 115 `df`, so
`--max_per_class` (default 250) caps how many images are sampled per risk
category for tractability on CPU -- it does NOT throw away whole classes,
every class still gets real images, just capped. With the default, expect
roughly 15-30 min for preprocessing+segmentation+handcrafted extraction on
~1250 images, plus CNN training time. Raise the cap for a stronger final
run once the pipeline's mechanics are confirmed; lower it (e.g. 40) for a
fast first pass. The CNN branch also gets `class_weight`-balanced training
and the classical classifiers use `class_weight="balanced"`, on top of the
capped sampling, since HAM10000's imbalance is severe enough that both
matter.

Outputs land in `--out_dir`:
- `results_summary_real.csv` -- accuracy/macro-precision/macro-recall
  ("sensitivity_recall")/macro-specificity/macro-F1/macro-AUC per
  classifier, **plus 3 ablations**: `metadata_only_baseline` (fast
  sanity-check floor), `cnn_only_ablation`, and
  `image_plus_abcd_no_metadata_ablation` (to show what the metadata branch
  specifically adds over image+ABCD alone)
- `results_by_skin_tone_proxy_real.xlsx` -- same metrics broken out per
  ITA skin-tone-proxy bucket, one sheet per classifier
- `per_class_report_<best_classifier>_real.csv` -- precision/recall/F1 per
  risk category for the best model (e.g. to check melanoma specifically
  isn't being under-detected even if aggregate accuracy looks fine)
- `feature_names_real.json` -- exact feature list per branch

## Swapping in a pretrained CNN backbone

`cnn_model.py` currently trains a small CNN from scratch (no external
weight downloads needed here). With internet access, replace `build_cnn()`
with a transfer-learning backbone for a real accuracy boost:

```python
base = tf.keras.applications.MobileNetV3Small(
    input_shape=(128,128,3), include_top=False, weights="imagenet", pooling="avg"
)
base.trainable = False  # or fine-tune the last few blocks
x = layers.Dense(64, activation="relu", name="deep_features")(base.output)
...
```

Everything downstream (handcrafted features, fusion, classical classifier,
stratified evaluation) stays the same.

## Requirements

```
tensorflow-cpu
scikit-learn
xgboost
opencv-python
scikit-image
numpy
pandas
matplotlib
openpyxl
```
