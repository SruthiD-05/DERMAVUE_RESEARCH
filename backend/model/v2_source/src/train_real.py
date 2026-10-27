"""
train_real.py
--------------
Full REAL-DATA hybrid pipeline: HAM10000 images + ABCD handcrafted features
+ patient metadata (age/sex/lesion localization), fused and classified into
5 risk categories (see metadata_features.RISK_CATEGORIES).

This is the genuine-data counterpart to train.py (which runs on the
synthetic demo set). Differences from train.py:
  - LESION-LEVEL train/val/test split (see real_dataset.py) -- HAM10000 has
    multiple images per physical lesion; splitting by image_id instead of
    lesion_id would leak the same lesion into both train and test and
    inflate test accuracy in a way that doesn't reflect real performance
  - 3 fused branches (deep CNN + handcrafted ABCD + metadata) instead of 2
  - 5-class softmax instead of binary sigmoid
  - CNN backbone is selectable: --backbone mobilenetv2 (ImageNet-pretrained,
    the default -- needs internet, i.e. Colab, not an offline sandbox) or
    --backbone scratch (tiny from-scratch CNN, works fully offline but
    needs far more data/epochs to learn good features)
  - skin-tone-proxy (ITA, estimated from perilesional skin -- see
    skin_tone_proxy.py) used for the stratified fairness evaluation,
    since HAM10000 ships no tone/Fitzpatrick ground truth
  - class-imbalance handling (nv=6705 vs df=115 in the raw data): capped
    per-class sampling for tractability, plus class-weighted CNN training
    and class-balanced classical classifiers

Run (from src/, after mounting Drive / downloading HAM10000 in Colab, with
Runtime > Change runtime type > T4 GPU enabled):
    python train_real.py \
        --metadata_csv "/content/drive/MyDrive/.../HAM10000_metadata.csv" \
        --images_dir   "/content/drive/MyDrive/.../ham10000_images_part_1" \
        --images_dir   "/content/drive/MyDrive/.../ham10000_images_part_2" \
        --out_dir ../outputs_real --max_per_class 400 --epochs 15

Runtime note: with max_per_class=400 (~2000 images across 5 classes) on a
T4 GPU, expect roughly 15-30 min total (image preprocessing/segmentation is
still CPU-bound and is usually the bigger share of that; CNN training
itself is fast on GPU). On CPU-only, expect significantly longer -- lower
--max_per_class for a first pass, raise it for the final run.
"""
import os
import time
import json
import argparse
import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_class_weight

from metadata_features import (
    load_metadata, fit_metadata_pipeline, transform_metadata,
    metadata_feature_names, RISK_CATEGORIES,
)
from real_dataset import load_real_dataset_split
from handcrafted_features import extract_handcrafted_features, FEATURE_NAMES as HC_FEATURE_NAMES
from cnn_model import (
    build_cnn_multiclass, build_cnn_multiclass_pretrained,
    train_cnn, get_feature_extractor, extract_deep_features,
)
from fusion_classifier import fuse_three_branches, build_classifiers_multiclass, fit_scaler
from evaluate import evaluate_overall_and_stratified_multiclass, fairness_gap, per_class_report


def _handcrafted_batch(images, masks):
    feats = [extract_handcrafted_features(images[i], masks[i]) for i in range(len(images))]
    return np.array(feats, dtype=np.float32)


def _build_cnn(backbone, img_size, n_classes, fine_tune):
    if backbone == "mobilenetv2":
        return build_cnn_multiclass_pretrained(
            input_shape=(img_size, img_size, 3), num_classes=n_classes, fine_tune=fine_tune
        )
    return build_cnn_multiclass(input_shape=(img_size, img_size, 3), num_classes=n_classes)


def main(metadata_csv, images_dirs, out_dir, img_size=128, epochs=15,
         max_per_class=400, batch_size=32, seed=42, backbone="mobilenetv2",
         fine_tune=False):
    os.makedirs(out_dir, exist_ok=True)
    t_start = time.time()
    n_classes = len(RISK_CATEGORIES)

    print("[1/7] Loading metadata + mapping to risk categories ...")
    df = load_metadata(metadata_csv)
    print(f"  {len(df)} total rows; class counts:\n{df['risk_category'].value_counts()}")

    print(f"\n[2/7] Lesion-level split + loading + preprocessing + segmenting "
          f"real images (backbone={backbone}, max_per_class={max_per_class}) ...")
    train_data, val_data, test_data = load_real_dataset_split(
        df, images_dirs, img_size=img_size, max_per_class=max_per_class, seed=seed
    )
    for tag, d in (("train", train_data), ("val", val_data), ("test", test_data)):
        print(f"  {tag}: {len(d['images'])} images loaded")
    print(f"  test-set skin-tone-proxy distribution:\n{pd.Series(test_data['tones']).value_counts()}")

    y_train, y_val, y_test = train_data["labels"], val_data["labels"], test_data["labels"]
    tones_test = test_data["tones"]
    meta_train, meta_val, meta_test = train_data["meta_df"], val_data["meta_df"], test_data["meta_df"]

    print("\n[3/7] Metadata-only baseline (fast sanity check before the slow branches) ...")
    meta_feat_train, meta_pipeline = fit_metadata_pipeline(meta_train)
    meta_feat_val = transform_metadata(meta_pipeline, meta_val)
    meta_feat_test = transform_metadata(meta_pipeline, meta_test)
    meta_only_clf = build_classifiers_multiclass()["random_forest"]
    meta_only_clf.fit(meta_feat_train, y_train)
    meta_only_prob = meta_only_clf.predict_proba(meta_feat_test)
    meta_only_pred = meta_only_prob.argmax(axis=1)
    meta_only_overall, _ = evaluate_overall_and_stratified_multiclass(
        y_test, meta_only_pred, meta_only_prob, tones_test, n_classes
    )
    print(f"  metadata_only (random_forest) acc={meta_only_overall['accuracy']:.3f} "
          f"macro_auc={meta_only_overall['auc']:.3f} -- this is your real-data floor; "
          "the full pipeline below should beat it.")

    print(f"\n[4/7] Training CNN branch on real images "
          f"(multiclass, backbone={backbone}, fine_tune={fine_tune}) ...")
    class_w = compute_class_weight("balanced", classes=np.arange(n_classes), y=y_train)
    class_weight = {i: w for i, w in enumerate(class_w)}
    print(f"  class weights (imbalance correction): {class_weight}")

    cnn = _build_cnn(backbone, img_size, n_classes, fine_tune)
    train_cnn(cnn, train_data["images"], y_train, val_data["images"], y_val,
              epochs=epochs, batch_size=batch_size, class_weight=class_weight,
              monitor="val_accuracy", mode="max")
    feature_extractor = get_feature_extractor(cnn)

    deep_train = extract_deep_features(feature_extractor, train_data["images"])
    deep_val = extract_deep_features(feature_extractor, val_data["images"])
    deep_test = extract_deep_features(feature_extractor, test_data["images"])

    print("\n[5/7] Extracting handcrafted ABCD + texture features ...")
    hc_train = _handcrafted_batch(train_data["images"], train_data["masks"])
    hc_val = _handcrafted_batch(val_data["images"], val_data["masks"])
    hc_test = _handcrafted_batch(test_data["images"], test_data["masks"])

    print("\n[6/7] Fusing all 3 branches (deep + handcrafted + metadata) "
          "and training + comparing classical classifiers ...")
    fused_train_raw = fuse_three_branches(deep_train, hc_train, meta_feat_train)
    fused_test_raw = fuse_three_branches(deep_test, hc_test, meta_feat_test)

    scaler = fit_scaler(fused_train_raw)
    fused_train = scaler.transform(fused_train_raw)
    fused_test = scaler.transform(fused_test_raw)

    classifiers = build_classifiers_multiclass()
    results_summary = [dict(meta_only_overall, classifier="metadata_only_baseline")]
    all_by_group = {}
    best_name, best_auc, best_pred = None, -1, None

    for name, clf in classifiers.items():
        clf.fit(fused_train, y_train)
        y_prob = clf.predict_proba(fused_test)
        y_pred = y_prob.argmax(axis=1)

        overall, by_group = evaluate_overall_and_stratified_multiclass(
            y_test, y_pred, y_prob, tones_test, n_classes
        )
        gap = fairness_gap(by_group, metric="accuracy")
        overall["skin_tone_accuracy_gap"] = gap
        overall["classifier"] = name
        results_summary.append(overall)
        all_by_group[name] = by_group

        print(f"  {name:15s} acc={overall['accuracy']:.3f} macro_auc={overall['auc']:.3f} "
              f"macro_sens={overall['sensitivity_recall']:.3f} macro_spec={overall['specificity']:.3f} "
              f"skin-tone-proxy acc gap={gap:.3f}")

        if overall["auc"] > best_auc:
            best_auc, best_name, best_pred = overall["auc"], name, y_pred

    # Ablations: CNN-alone (no fusion), and image-only fusion (no metadata
    # branch) -- these two numbers are the evidence that (a) the classical
    # fusion step helps over the raw CNN, and (b) the metadata branch adds
    # something beyond image+ABCD alone.
    cnn_prob_test = cnn.predict(test_data["images"], verbose=0)
    cnn_pred_test = cnn_prob_test.argmax(axis=1)
    cnn_overall, cnn_by_group = evaluate_overall_and_stratified_multiclass(
        y_test, cnn_pred_test, cnn_prob_test, tones_test, n_classes
    )
    cnn_overall["skin_tone_accuracy_gap"] = fairness_gap(cnn_by_group, metric="accuracy")
    cnn_overall["classifier"] = f"cnn_only_ablation_{backbone}"
    results_summary.append(cnn_overall)
    all_by_group[f"cnn_only_ablation_{backbone}"] = cnn_by_group
    print(f"  {'cnn_only (ablation)':15s} acc={cnn_overall['accuracy']:.3f} "
          f"macro_auc={cnn_overall['auc']:.3f} skin-tone-proxy acc gap={cnn_overall['skin_tone_accuracy_gap']:.3f}")

    no_meta_scaler = fit_scaler(np.concatenate([deep_train, hc_train], axis=1))
    no_meta_train_scaled = no_meta_scaler.transform(np.concatenate([deep_train, hc_train], axis=1))
    no_meta_test_scaled = no_meta_scaler.transform(np.concatenate([deep_test, hc_test], axis=1))
    no_meta_clf = build_classifiers_multiclass()["xgboost"]
    no_meta_clf.fit(no_meta_train_scaled, y_train)
    no_meta_prob = no_meta_clf.predict_proba(no_meta_test_scaled)
    no_meta_pred = no_meta_prob.argmax(axis=1)
    no_meta_overall, no_meta_by_group = evaluate_overall_and_stratified_multiclass(
        y_test, no_meta_pred, no_meta_prob, tones_test, n_classes
    )
    no_meta_overall["skin_tone_accuracy_gap"] = fairness_gap(no_meta_by_group, metric="accuracy")
    no_meta_overall["classifier"] = "image_plus_abcd_no_metadata_ablation"
    results_summary.append(no_meta_overall)
    all_by_group["image_plus_abcd_no_metadata_ablation"] = no_meta_by_group
    print(f"  {'image+ABCD only':15s} acc={no_meta_overall['accuracy']:.3f} "
          f"macro_auc={no_meta_overall['auc']:.3f} (compare to '{best_name}' above to see what metadata adds)")

    print(f"\n[7/7] Best fused (3-branch) model by macro-AUC: {best_name} "
          f"(macro-AUC={best_auc:.3f}). Saving outputs ...")

    summary_df = pd.DataFrame(results_summary).set_index("classifier")
    summary_df.to_csv(os.path.join(out_dir, "results_summary_real.csv"))

    with pd.ExcelWriter(os.path.join(out_dir, "results_by_skin_tone_proxy_real.xlsx")) as writer:
        for name, gdf in all_by_group.items():
            if not gdf.empty:
                gdf.to_excel(writer, sheet_name=name[:31])

    best_report = per_class_report(y_test, best_pred, RISK_CATEGORIES)
    best_report.to_csv(os.path.join(out_dir, f"per_class_report_{best_name}_real.csv"))

    with open(os.path.join(out_dir, "feature_names_real.json"), "w") as f:
        json.dump({
            "backbone": backbone,
            "cnn_deep_features": 64,
            "handcrafted_features": HC_FEATURE_NAMES,
            "metadata_features": metadata_feature_names(meta_pipeline),
            "risk_categories": RISK_CATEGORIES,
        }, f, indent=2)

    elapsed = time.time() - t_start
    print(f"\nDone in {elapsed/60:.1f} min. See:")
    print(f"  {os.path.join(out_dir, 'results_summary_real.csv')}")
    print(f"  {os.path.join(out_dir, 'results_by_skin_tone_proxy_real.xlsx')}")
    print(f"  {os.path.join(out_dir, f'per_class_report_{best_name}_real.csv')}")
    print(f"  {os.path.join(out_dir, 'feature_names_real.json')}")
    print("\nIMPORTANT for your write-up:")
    print("  - Train/val/test are split by lesion_id, not image_id, so the same")
    print("    physical lesion never appears in more than one split (no leakage).")
    print("  - skin_tone_proxy is an ITA-based estimate from perilesional skin pixels,")
    print("    NOT a ground-truth Fitzpatrick/ethnicity label -- HAM10000 has none.")
    return summary_df, all_by_group


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata_csv", required=True, help="Path to HAM10000_metadata.csv")
    parser.add_argument("--images_dir", action="append", required=True,
                         help="Folder containing <image_id>.jpg files. Pass twice "
                              "(once per HAM10000 image part folder).")
    parser.add_argument("--out_dir", default="../outputs_real")
    parser.add_argument("--img_size", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--max_per_class", type=int, default=400,
                         help="Cap images per risk category, applied independently within "
                              "train/val/test after the lesion-level split. 0 = no cap.")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--backbone", choices=["mobilenetv2", "scratch"], default="mobilenetv2",
                         help="mobilenetv2 = ImageNet-pretrained transfer learning (needs internet, "
                              "recommended). scratch = tiny from-scratch CNN (fully offline, weaker).")
    parser.add_argument("--fine_tune", action="store_true",
                         help="Unfreeze the last few MobileNetV2 layers (mobilenetv2 backbone only). "
                              "Ignored for --backbone scratch.")
    args = parser.parse_args()

    main(
        metadata_csv=args.metadata_csv,
        images_dirs=args.images_dir,
        out_dir=args.out_dir,
        img_size=args.img_size,
        epochs=args.epochs,
        max_per_class=(args.max_per_class or None),
        batch_size=args.batch_size,
        seed=args.seed,
        backbone=args.backbone,
        fine_tune=args.fine_tune,
    )
