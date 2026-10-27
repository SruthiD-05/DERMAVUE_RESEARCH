"""
real_dataset.py
----------------
Loads real HAM10000 images and produces a LESION-LEVEL train/val/test split.

Why lesion-level, not image-level: HAM10000 contains multiple photos of the
same physical lesion (linked by `lesion_id` -- different angles/times/zoom).
Splitting at the IMAGE level lets the same lesion appear in both train and
test, so the model can partly memorize lesion-specific artifacts instead of
learning generalizable diagnostic features -- this inflates test accuracy in
a way that will not hold up on a truly unseen lesion (or under viva
questioning). This module splits UNIQUE lesion_ids first, then every image
of a given lesion is guaranteed to land in only one of train/val/test.

Per-class capping (for CPU/GPU-time tractability) happens AFTER the lesion
split, independently within each split, so it never moves a lesion across
splits.
"""
import os
import glob
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from preprocessing import preprocess_image
from segmentation import segment_lesion
from skin_tone_proxy import estimate_skin_tone


def build_image_index(image_dirs):
    """Maps image_id -> full file path by scanning all provided directories."""
    index = {}
    for d in image_dirs:
        for fpath in glob.glob(os.path.join(d, "*.jpg")):
            image_id = os.path.splitext(os.path.basename(fpath))[0]
            index[image_id] = fpath
    return index


def _safe_split_ids(ids, test_size, seed, strata):
    """train_test_split with a fallback to unstratified if some class has
    too few unique LESIONS to stratify at the requested ratio (can happen
    for the smallest classes at aggressive splits/caps)."""
    try:
        return train_test_split(ids, test_size=test_size, random_state=seed, stratify=strata)
    except ValueError:
        return train_test_split(ids, test_size=test_size, random_state=seed)


def lesion_level_split(df, test_size=0.2, val_size=0.15, seed=42):
    """Splits unique lesion_ids into train/val/test (stratified by that
    lesion's risk_category), then returns boolean row-masks so every image
    of a given lesion stays together in the same split."""
    lesion_labels = df.groupby("lesion_id")["risk_category"].first()
    lesion_ids = lesion_labels.index.values
    labels = lesion_labels.values

    train_ids, test_ids = _safe_split_ids(lesion_ids, test_size, seed, labels)
    train_labels = lesion_labels.loc[train_ids].values
    train_ids, val_ids = _safe_split_ids(train_ids, val_size, seed, train_labels)

    train_mask = df["lesion_id"].isin(train_ids)
    val_mask = df["lesion_id"].isin(val_ids)
    test_mask = df["lesion_id"].isin(test_ids)
    return train_mask, val_mask, test_mask


def cap_per_class(df, max_per_class, seed=42):
    """Samples up to max_per_class ROWS per risk_category within a single
    split (train/val/test are capped independently, after the lesion-level
    split above, so this never introduces leakage)."""
    if not max_per_class:
        return df.reset_index(drop=True)
    parts = []
    for cat, group in df.groupby("risk_category"):
        n = min(len(group), max_per_class)
        parts.append(group.sample(n=n, random_state=seed))
    return pd.concat(parts, axis=0).sample(frac=1.0, random_state=seed).reset_index(drop=True)


def _load_images_for_rows(sub_df, image_index, img_size, progress_every=100, tag=""):
    images, masks, labels, tones, paths, kept_rows = [], [], [], [], [], []
    missing = 0
    t0 = time.time()
    n = len(sub_df)
    for i, row in enumerate(sub_df.itertuples(index=False)):
        image_id = getattr(row, "image_id")
        fpath = image_index.get(image_id)
        if fpath is None:
            missing += 1
            continue
        try:
            img = preprocess_image(fpath, size=img_size)
            mask, _ = segment_lesion(img)
            tone, _ita = estimate_skin_tone(img, mask)
        except Exception as e:
            missing += 1
            continue

        images.append(img)
        masks.append(mask)
        labels.append(getattr(row, "risk_label"))
        tones.append(tone)
        paths.append(fpath)
        kept_rows.append(row)

        if (i + 1) % progress_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            print(f"  [{tag}] ...{i+1}/{n} images ({rate:.1f} img/s, "
                  f"~{(n-i-1)/max(rate,1e-6):.0f}s left)")

    if missing:
        print(f"  [{tag}] warning: {missing} rows skipped (missing file or read/segmentation error)")

    meta_df = pd.DataFrame(kept_rows).reset_index(drop=True)
    return {
        "images": np.array(images, dtype=np.uint8),
        "masks": masks,
        "labels": np.array(labels, dtype=np.int32),
        "tones": np.array(tones),
        "meta_df": meta_df,
        "paths": np.array(paths),
    }


def load_real_dataset_split(df, image_dirs, img_size=128, max_per_class=250, seed=42):
    """
    Full leakage-safe pipeline: lesion-level split -> per-class cap (within
    each split) -> image loading + segmentation + skin-tone-proxy, done
    separately per split so val/test never see a lesion from train.

    Args:
        df: output of metadata_features.load_metadata() (has risk_category,
            risk_label, lesion_id, image_id columns).
        image_dirs: list of folders to search for <image_id>.jpg
        max_per_class: cap rows per risk_category, applied independently
            within train/val/test. 0/None = no cap (use all).

    Returns:
        (train, val, test), each a dict:
        {"images", "masks", "labels", "tones", "meta_df", "paths"}
    """
    df = df.dropna(subset=["lesion_id", "image_id", "risk_category"]).reset_index(drop=True)
    train_mask, val_mask, test_mask = lesion_level_split(df, seed=seed)

    n_lesions = df["lesion_id"].nunique()
    print(f"  lesion-level split: "
          f"{df[train_mask]['lesion_id'].nunique()} train / "
          f"{df[val_mask]['lesion_id'].nunique()} val / "
          f"{df[test_mask]['lesion_id'].nunique()} test lesions "
          f"(of {n_lesions} total) -- no lesion appears in more than one split")

    df_train = cap_per_class(df[train_mask], max_per_class, seed=seed)
    df_val = cap_per_class(df[val_mask], max_per_class, seed=seed)
    df_test = cap_per_class(df[test_mask], max_per_class, seed=seed)
    print(f"  after per-class cap (max_per_class={max_per_class}): "
          f"{len(df_train)} train / {len(df_val)} val / {len(df_test)} test rows")

    image_index = build_image_index(image_dirs)
    print(f"  indexed {len(image_index)} image files across {len(image_dirs)} folder(s)")

    train_data = _load_images_for_rows(df_train, image_index, img_size, tag="train")
    val_data = _load_images_for_rows(df_val, image_index, img_size, tag="val")
    test_data = _load_images_for_rows(df_test, image_index, img_size, tag="test")
    return train_data, val_data, test_data
