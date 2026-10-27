"""
metadata_features.py
---------------------
Third branch of the hybrid model (alongside the CNN image branch and the
ABCD handcrafted-feature branch): turns the patient metadata that ships
with HAM10000 (age, sex, lesion localization) into a numeric feature
vector that can be fused with the other two branches.

Also defines the 5-class risk-category mapping used across the whole
real-data pipeline (train_real.py, real_dataset.py, evaluate.py), so the
CNN head, the classical classifiers, and the reporting all agree on the
same label set/order.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

# HAM10000's 7 `dx` diagnosis codes collapsed into 5 clinically-motivated
# risk categories. Order matters: RISK_CATEGORIES fixes the integer label
# used everywhere downstream (CNN softmax index, confusion matrix axes).
DX_TO_CATEGORY = {
    "nv":    "Normal Skin",
    "bkl":   "Skin Allergy/Acne",
    "df":    "Skin Allergy/Acne",
    "vasc":  "Suspicious Lesion",
    "akiec": "Suspicious Lesion",
    "bcc":   "Possible Skin Cancer (Basal Cell Carcinoma)",
    "mel":   "Possible Skin Cancer (Melanoma)",
}

RISK_CATEGORIES = [
    "Normal Skin",
    "Skin Allergy/Acne",
    "Suspicious Lesion",
    "Possible Skin Cancer (Basal Cell Carcinoma)",
    "Possible Skin Cancer (Melanoma)",
]
LABEL_TO_IDX = {name: i for i, name in enumerate(RISK_CATEGORIES)}
IDX_TO_LABEL = {i: name for name, i in LABEL_TO_IDX.items()}

NUMERIC_META = ["age"]
CATEGORICAL_META = ["sex", "localization"]


def load_metadata(csv_path):
    """Reads HAM10000_metadata.csv and adds risk_category + risk_label columns."""
    df = pd.read_csv(csv_path)
    df["risk_category"] = df["dx"].map(DX_TO_CATEGORY)
    df["risk_label"] = df["risk_category"].map(LABEL_TO_IDX)
    unmapped = df["risk_category"].isna().sum()
    if unmapped:
        print(f"  warning: {unmapped} rows had an unrecognized dx code and were dropped")
        df = df.dropna(subset=["risk_category"]).reset_index(drop=True)
    return df


def build_metadata_pipeline():
    """ColumnTransformer: impute+scale age, impute+one-hot sex/localization."""
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    pipeline = ColumnTransformer([
        ("num", numeric_pipe, NUMERIC_META),
        ("cat", categorical_pipe, CATEGORICAL_META),
    ])
    return pipeline


def fit_metadata_pipeline(df_train):
    """Fits the pipeline on TRAIN rows only (avoids leaking val/test statistics)."""
    pipeline = build_metadata_pipeline()
    features = pipeline.fit_transform(df_train[NUMERIC_META + CATEGORICAL_META])
    if hasattr(features, "toarray"):
        features = features.toarray()
    return np.asarray(features, dtype=np.float32), pipeline


def transform_metadata(pipeline, df):
    """Transforms val/test (or any) rows with an already-fitted pipeline."""
    features = pipeline.transform(df[NUMERIC_META + CATEGORICAL_META])
    if hasattr(features, "toarray"):
        features = features.toarray()
    return np.asarray(features, dtype=np.float32)


def metadata_feature_names(pipeline):
    try:
        return list(pipeline.get_feature_names_out())
    except Exception:
        return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="HAM10000_metadata.csv")
    args = parser.parse_args()

    df = load_metadata(args.csv)
    print("Rows loaded:", len(df))
    print("\nOriginal diagnosis counts (dx column):")
    print(df["dx"].value_counts())
    print("\nMapped to project risk categories:")
    print(df["risk_category"].value_counts())

    feats, pipeline = fit_metadata_pipeline(df)
    print(f"\nMetadata feature matrix shape: {feats.shape}")
    print(feats[0])
