"""
skin_tone_proxy.py
-------------------
HAM10000 ships no skin-tone / Fitzpatrick labels, but the whole point of
this project (per README) is to report accuracy PER skin-tone group, not
just in aggregate. Without ground-truth labels, the documented, literature-
standard workaround is to estimate the Individual Typology Angle (ITA)
from the pixels of the healthy skin surrounding the lesion (Del Bino &
Bernerd's ITA scale, widely used as an objective pigmentation proxy).

    ITA = arctan((L* - 50) / b*) * 180 / pi      (CIE-LAB color space)

Higher ITA = lighter skin, lower/negative ITA = darker skin. This is
CLEARLY a proxy, not ground truth or self-reported ethnicity/Fitzpatrick
type, and must be reported as such (see README + any write-up).

Bucket thresholds follow the standard 6-band ITA scale from the
dermatology literature.
"""
import cv2
import numpy as np

ITA_BANDS = [
    (55, float("inf"), "very_light"),
    (41, 55, "light"),
    (28, 41, "intermediate"),
    (10, 28, "tan"),
    (-30, 10, "brown"),
    (float("-inf"), -30, "dark"),
]


def _ita_bucket(ita_value):
    for lo, hi, name in ITA_BANDS:
        if lo <= ita_value < hi:
            return name
    return "unknown"


def estimate_skin_tone(img_bgr, lesion_mask):
    """
    Estimates a skin-tone-proxy bucket from the healthy skin surrounding
    the lesion (i.e. the pixels NOT covered by lesion_mask).

    Returns (bucket_name: str, ita_value: float).
    """
    surrounding = (lesion_mask == 0)
    # Also drop near-black pixels (corner vignettes / borders / dermoscope
    # ring artifacts common in HAM10000 images), which would bias ITA hard.
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    valid = surrounding & (gray > 20)

    if valid.sum() < 50:
        # Fall back to the full image if the lesion covers almost everything.
        valid = gray > 20
        if valid.sum() < 50:
            return "unknown", float("nan")

    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    # OpenCV LAB: L in [0,255] -> scale to [0,100]; a,b already centered ~128.
    L = lab[:, :, 0][valid] * (100.0 / 255.0)
    b = lab[:, :, 2][valid] - 128.0

    b_safe = np.where(np.abs(b) < 1e-3, 1e-3, b)
    ita = np.degrees(np.arctan((L.mean() - 50.0) / np.mean(b_safe)))
    return _ita_bucket(ita), float(ita)
