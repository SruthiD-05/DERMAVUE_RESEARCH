"""
Skin cancer triage — inference engine (final tri-modal model).

Pipeline (identical to the training notebook):
  photo -> DullRazor hair removal -> ITA skin tone -> Shades-of-Gray colour constancy -> 384x384
  Stream 1: 3 CNNs (EffNet-B4, EffNetV2-S, EffNet-B4 seed 7), 7-class softmax, TTA,
            P(malignant) = P(mel) + P(bcc) + P(akiec)
  Stream 2+3: ABCD/texture features + patient metadata -> XGBoost
  Fusion: logistic-regression stacker on the logits of all streams
  Several photos of the SAME lesion -> fused scores are averaged (lesion-level decision)
"""
import json
import math
import os
import time

import cv2
import numpy as np
from xgboost import XGBClassifier

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import tensorflow as tf  # noqa: E402
from tensorflow import keras  # noqa: E402


# ---------------- preprocessing (copied exactly from the training notebook) ----------------
def dull_razor(img_rgb):
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT,
                          cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))
    _, mask = cv2.threshold(bh, 10, 255, cv2.THRESH_BINARY)
    return cv2.inpaint(img_rgb, mask, 1, cv2.INPAINT_TELEA)


def shades_of_gray(img_rgb, p=6):
    f = img_rgb.astype(np.float32)
    illum = np.power(np.mean(np.power(f, p), axis=(0, 1)), 1.0 / p)
    illum = illum / (np.linalg.norm(illum) + 1e-6)
    f = f / (illum * np.sqrt(3) + 1e-6)
    return np.clip(f, 0, 255).astype(np.uint8)


def ita_angle(img_rgb):
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    L = lab[:, :, 0] * (100.0 / 255.0)
    b = lab[:, :, 2] - 128.0
    v = np.abs(b) > 0.01
    return float(np.mean(np.arctan2(L[v] - 50, b[v])) * 180 / np.pi)


def tone_label(ita):
    if ita > 41:   return 'Type I-II (Light)'
    elif ita > 28: return 'Type III (Intermediate)'
    elif ita > 10: return 'Type IV (Tan)'
    else:          return 'Type V-VI (Dark)'


def preprocess(rgb, size):
    h, w = rgb.shape[:2]
    if max(h, w) > 600:
        s = 600 / max(h, w)
        rgb = cv2.resize(rgb, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    clean = dull_razor(rgb)
    tone = tone_label(ita_angle(clean))
    img = cv2.resize(shades_of_gray(clean), (size, size), interpolation=cv2.INTER_AREA)
    return img, tone


def abcd_features(u):
    g = cv2.cvtColor(u, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(u, cv2.COLOR_RGB2HSV)
    _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    cs, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cs:
        c = max(cs, key=cv2.contourArea)
        a = cv2.contourArea(c); p = cv2.arcLength(c, True)
        comp = p ** 2 / (4 * math.pi * max(a, 1))
        diam = math.sqrt(4 * a / math.pi)
    else:
        comp, diam, a = 1.0, 0.0, 0.0
    return [np.std(u[:, :, 0]), np.std(u[:, :, 1]), np.std(u[:, :, 2]),
            np.std(hsv[:, :, 0]), np.std(hsv[:, :, 1]),
            comp, diam, a, cv2.Laplacian(g, cv2.CV_64F).var()]


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


class SkinCancerModel:
    def __init__(self, model_dir, tta_views=None):
        with open(os.path.join(model_dir, "config.json")) as f:
            self.cfg = json.load(f)
        c = self.cfg
        self.img = c["IMG"]
        self.mal_idx = c["MAL_IDX"]
        self.cnn_names = c["CNN_NAMES"]
        self.tta_views = int(tta_views or os.environ.get("TTA_VIEWS", c.get("TTA_VIEWS", 8)))
        self.cnns = [keras.models.load_model(os.path.join(model_dir, f"{n}.keras"), compile=False)
                     for n in self.cnn_names]
        self.xgb = XGBClassifier()
        self.xgb.load_model(os.path.join(model_dir, "xgb_tabular.json"))
        self.stack_coef = np.array(c["STACK_COEF"], dtype=np.float64)
        self.stack_intercept = float(c["STACK_INTERCEPT"])
        self.locs = c["LOCS"]
        self.uv_sites = c["UV_SITES"]
        self.age_med = c["AGE_MED"]

    # TTA views exactly as in training: rotations k = 0..3, each with a horizontal flip
    def _views(self, x):
        views = []
        for k in range(self.tta_views // 2):
            r = np.rot90(x, k, axes=(1, 2))
            views += [r, r[:, :, ::-1]]
        return views

    def _cnn_class_probs(self, X):
        """Return each CNN's seven-class softmax output.

        The trained fusion stacker does not consume these seven-class vectors
        directly; it consumes the malignant aggregate from each CNN. Keeping
        that distinction explicit prevents auxiliary CNN scores from being
        presented as a final multiclass diagnosis.
        """
        out = []
        for m in self.cnns:
            p7 = np.mean([m.predict(np.ascontiguousarray(v).astype(np.float32), verbose=0)
                          for v in self._views(X)], axis=0)
            out.append(p7)
        return out  # list (one per CNN) of arrays (n_images, 7)

    def _meta(self, age, sex, localization):
        age = self.age_med if age is None else float(age)
        sex = 1.0 if str(sex).lower() == "male" else 0.0
        loc = (localization or "unknown").lower()
        uv = 1.0 if any(k in loc for k in self.uv_sites) else 0.0
        onehot = [1.0 if loc == l else 0.0 for l in self.locs]
        return [age / 100.0, sex, uv] + onehot

    def predict(self, images_rgb, age=None, sex=None, localization=None):
        """images_rgb: list of RGB uint8 arrays, all photos of ONE lesion."""
        t0 = time.time()
        proc = [preprocess(im, self.img) for im in images_rgb]
        X = np.stack([p[0] for p in proc])
        tones = [p[1] for p in proc]

        cnn_class_probs = self._cnn_class_probs(X)
        cnn = [p7[:, self.mal_idx].sum(axis=1) for p7 in cnn_class_probs]
        meta = self._meta(age, sex, localization)
        T = np.array([abcd_features(u) + meta for u in X], dtype=np.float32)
        p_tab = self.xgb.predict_proba(T)[:, 1]

        Z = np.column_stack([logit(p) for p in cnn] + [logit(p_tab)])
        fused_per_image = 1.0 / (1.0 + np.exp(-(Z @ self.stack_coef + self.stack_intercept)))
        score = float(np.mean(fused_per_image))          # lesion-level decision
        auxiliary_class_scores = np.mean(
            [np.mean(p7, axis=0) for p7 in cnn_class_probs], axis=0
        )

        t_acc, t_scr = self.cfg["T_ACC"], self.cfg["T_SCR"]
        if score >= t_acc:
            risk = "HIGH"
        elif score >= t_scr:
            risk = "MODERATE"
        else:
            risk = "LOW"
        return {
            "prediction": "MALIGNANT" if score >= t_acc else "BENIGN",
            "screening_flag": bool(score >= t_scr),
            "risk_level": risk,
            "malignancy_score": round(score, 4),
            "thresholds": {"balanced": t_acc, "screening": t_scr},
            "skin_tone_ita": tones[0],
            "num_images": len(images_rgb),
            "stream_scores": {
                **{n: round(float(np.mean(p)), 4) for n, p in zip(self.cnn_names, cnn)},
                "ABCD+metadata": round(float(np.mean(p_tab)), 4),
            },
            "auxiliary_class_scores": {
                label: round(float(value), 4)
                for label, value in zip(self.cfg["DX"], auxiliary_class_scores)
            },
            "auxiliary_class_score_semantics": (
                "Mean of the three CNN seven-class softmax outputs. These are "
                "auxiliary model scores, not the final fused multiclass output, "
                "not calibrated probabilities, and not a subtype diagnosis."
            ),
            "inference_seconds": round(time.time() - t0, 2),
            "disclaimer": "Research prototype for decision support only. Not a medical diagnosis.",
        }
