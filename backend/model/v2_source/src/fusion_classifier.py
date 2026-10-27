"""
fusion_classifier.py
---------------------
Step 5 of the methodology: fuse the CNN deep-feature branch with the
handcrafted ABCD/texture branch, then train a classical ML classifier
(XGBoost, with SVM/RandomForest as comparison baselines) on the fused
vector. This is the "hybrid" part of the hybrid model: deep representation
learning + classical decision boundary, rather than an end-to-end CNN
softmax classifier alone.
"""
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier


def fuse_features(deep_features, handcrafted_features):
    """Concatenate and z-score the two feature branches."""
    fused = np.concatenate([deep_features, handcrafted_features], axis=1)
    return fused


def fuse_three_branches(deep_features, handcrafted_features, metadata_features):
    """Concatenates all three branches (image CNN + ABCD handcrafted +
    patient metadata) used by the real-data 5-class pipeline (train_real.py)."""
    return np.concatenate([deep_features, handcrafted_features, metadata_features], axis=1)


def build_classifiers_multiclass():
    """Same three classifiers as build_classifiers(), tuned for the 5-class
    real-data risk categories (multiclass eval_metric for xgboost, larger
    forests since the fused feature vector is bigger with metadata added)."""
    return {
        "svm_rbf": SVC(kernel="rbf", probability=True, C=2.0, class_weight="balanced", random_state=0),
        "random_forest": RandomForestClassifier(n_estimators=400, max_depth=10, class_weight="balanced", random_state=0),
        "xgboost": XGBClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.06,
            subsample=0.9, colsample_bytree=0.9, eval_metric="mlogloss", random_state=0,
        ),
    }


def build_classifiers():
    """Returns a dict of classical classifiers to compare on the fused features."""
    return {
        "svm_rbf": SVC(kernel="rbf", probability=True, C=2.0, class_weight="balanced", random_state=0),
        "random_forest": RandomForestClassifier(n_estimators=300, max_depth=8, class_weight="balanced", random_state=0),
        "xgboost": XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.08,
            subsample=0.9, colsample_bytree=0.9, eval_metric="logloss", random_state=0,
        ),
    }


def fit_scaler(fused_train):
    scaler = StandardScaler()
    scaler.fit(fused_train)
    return scaler
