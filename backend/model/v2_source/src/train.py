"""
train.py
--------
Orchestrates the full hybrid melanoma-detection pipeline:

  1. Load images (+ segment lesion masks)                [dataset.py]
  2. Train the CNN branch, extract deep features          [cnn_model.py]
  3. Extract handcrafted ABCD/texture features             [handcrafted_features.py]
  4. Fuse both feature sets                                 [fusion_classifier.py]
  5. Train + compare classical classifiers on fused features
  6. Evaluate overall AND stratified by skin-tone group     [evaluate.py]

Run:
    python train.py --data_dir ../data/synthetic_dataset --out_dir ../outputs

Using real data: point --data_dir at a folder structured as
    <root>/benign/<tone_group>/*.jpg
    <root>/melanoma/<tone_group>/*.jpg
(see README.md "Using real data").
"""
import os
import argparse
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from dataset import load_dataset
from handcrafted_features import extract_handcrafted_features, FEATURE_NAMES
from cnn_model import build_cnn, train_cnn, get_feature_extractor, extract_deep_features
from fusion_classifier import fuse_features, build_classifiers, fit_scaler
from evaluate import evaluate_overall_and_stratified, fairness_gap


def main(data_dir, out_dir, img_size=128, epochs=15, seed=42):
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.RandomState(seed)

    print(f"[1/6] Loading + segmenting images from {data_dir} ...")
    images, masks, labels, skin_tones, paths = load_dataset(data_dir, img_size=img_size)
    print(f"  loaded {len(images)} images | class balance: "
          f"benign={int((labels==0).sum())} melanoma={int((labels==1).sum())}")

    # Stratify split by class AND skin tone so every tone group appears in
    # both train and test sets (needed for meaningful stratified evaluation).
    strata = np.array([f"{l}_{t}" for l, t in zip(labels, skin_tones)])
    idx = np.arange(len(images))
    idx_train, idx_test = train_test_split(
        idx, test_size=0.25, random_state=seed, stratify=strata
    )
    idx_train, idx_val = train_test_split(
        idx_train, test_size=0.15, random_state=seed, stratify=strata[idx_train]
    )

    X_train, y_train = images[idx_train], labels[idx_train]
    X_val, y_val = images[idx_val], labels[idx_val]
    X_test, y_test = images[idx_test], labels[idx_test]
    tones_test = skin_tones[idx_test]

    print(f"  train={len(idx_train)} val={len(idx_val)} test={len(idx_test)}")

    print("[2/6] Training CNN branch ...")
    cnn = build_cnn(input_shape=(img_size, img_size, 3))
    train_cnn(cnn, X_train, y_train, X_val, y_val, epochs=epochs)
    feature_extractor = get_feature_extractor(cnn)

    deep_train = extract_deep_features(feature_extractor, X_train)
    deep_val = extract_deep_features(feature_extractor, X_val)
    deep_test = extract_deep_features(feature_extractor, X_test)

    print("[3/6] Extracting handcrafted ABCD + texture features ...")
    def handcrafted_batch(idxs):
        feats = []
        for i in idxs:
            feats.append(extract_handcrafted_features(images[i], masks[i]))
        return np.array(feats, dtype=np.float32)

    hc_train = handcrafted_batch(idx_train)
    hc_val = handcrafted_batch(idx_val)
    hc_test = handcrafted_batch(idx_test)

    print("[4/6] Fusing deep + handcrafted features ...")
    fused_train_raw = fuse_features(deep_train, hc_train)
    fused_val_raw = fuse_features(deep_val, hc_val)
    fused_test_raw = fuse_features(deep_test, hc_test)

    scaler = fit_scaler(fused_train_raw)
    fused_train = scaler.transform(fused_train_raw)
    fused_val = scaler.transform(fused_val_raw)
    fused_test = scaler.transform(fused_test_raw)

    print("[5/6] Training + comparing classical classifiers on fused features ...")
    classifiers = build_classifiers()
    results_summary = []
    all_by_group = {}
    best_name, best_auc, best_clf = None, -1, None

    for name, clf in classifiers.items():
        clf.fit(fused_train, y_train)
        y_prob = clf.predict_proba(fused_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        overall, by_group = evaluate_overall_and_stratified(y_test, y_pred, y_prob, tones_test)
        gap = fairness_gap(by_group, metric="accuracy")
        overall["skin_tone_accuracy_gap"] = gap
        overall["classifier"] = name
        results_summary.append(overall)
        all_by_group[name] = by_group

        print(f"  {name:15s} acc={overall['accuracy']:.3f} auc={overall['auc']:.3f} "
              f"sens={overall['sensitivity_recall']:.3f} spec={overall['specificity']:.3f} "
              f"skin-tone acc gap={gap:.3f}")

        if overall["auc"] > best_auc:
            best_auc, best_name, best_clf = overall["auc"], name, clf

    # Also evaluate the CNN branch alone (no handcrafted fusion, no classical
    # classifier) as an ablation baseline, to show what fusion adds.
    cnn_prob_test = cnn.predict(X_test, verbose=0).ravel()
    cnn_pred_test = (cnn_prob_test >= 0.5).astype(int)
    cnn_overall, cnn_by_group = evaluate_overall_and_stratified(y_test, cnn_pred_test, cnn_prob_test, tones_test)
    cnn_overall["skin_tone_accuracy_gap"] = fairness_gap(cnn_by_group, metric="accuracy")
    cnn_overall["classifier"] = "cnn_only_ablation"
    results_summary.append(cnn_overall)
    all_by_group["cnn_only_ablation"] = cnn_by_group
    print(f"  {'cnn_only (ablation)':15s} acc={cnn_overall['accuracy']:.3f} "
          f"auc={cnn_overall['auc']:.3f} skin-tone acc gap={cnn_overall['skin_tone_accuracy_gap']:.3f}")

    print(f"[6/6] Best fused model by AUC: {best_name} (AUC={best_auc:.3f}). Saving outputs ...")

    summary_df = pd.DataFrame(results_summary).set_index("classifier")
    summary_df.to_csv(os.path.join(out_dir, "results_summary.csv"))

    with pd.ExcelWriter(os.path.join(out_dir, "results_by_skin_tone.xlsx")) as writer:
        for name, df in all_by_group.items():
            if not df.empty:
                df.to_excel(writer, sheet_name=name[:31])

    with open(os.path.join(out_dir, "feature_names.json"), "w") as f:
        json.dump({"cnn_deep_features": 64, "handcrafted_features": FEATURE_NAMES}, f, indent=2)

    print("Done. See:")
    print(f"  {os.path.join(out_dir, 'results_summary.csv')}")
    print(f"  {os.path.join(out_dir, 'results_by_skin_tone.xlsx')}")
    return summary_df, all_by_group


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="../data/synthetic_dataset")
    parser.add_argument("--out_dir", default="../outputs")
    parser.add_argument("--img_size", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=15)
    args = parser.parse_args()
    main(args.data_dir, args.out_dir, img_size=args.img_size, epochs=args.epochs)
