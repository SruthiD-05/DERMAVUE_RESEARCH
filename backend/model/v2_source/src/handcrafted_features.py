"""
handcrafted_features.py
------------------------
Step 4 (classical branch) of the methodology: extract clinically-grounded
handcrafted features based on the dermatology "ABCD rule":
    A - Asymmetry
    B - Border irregularity
    C - Color variation
    D - Diameter (size)
plus GLCM texture descriptors, using the lesion mask from segmentation.py.

These features are concatenated with the CNN's deep feature vector in
fusion_classifier.py to form the hybrid representation.
"""
import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

FEATURE_NAMES = [
    "asymmetry", "border_compactness", "color_std_b", "color_std_g", "color_std_r",
    "color_std_h", "color_std_s", "color_std_v", "n_distinct_color_clusters",
    "diameter_px", "area_px",
    "glcm_contrast", "glcm_homogeneity", "glcm_energy", "glcm_correlation",
]


def _asymmetry_score(mask):
    """Compares lesion area on either side of its centroid, both axes.
    0 = perfectly symmetric, higher = more asymmetric."""
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return 0.0
    cx, cy = int(xs.mean()), int(ys.mean())
    h, w = mask.shape

    left = mask[:, :cx] > 0
    right = mask[:, cx:] > 0
    right_flipped = np.fliplr(right)
    min_w = min(left.shape[1], right_flipped.shape[1])
    horiz_diff = np.logical_xor(left[:, -min_w:], right_flipped[:, :min_w]).sum()

    top = mask[:cy, :] > 0
    bottom = mask[cy:, :] > 0
    bottom_flipped = np.flipud(bottom)
    min_h = min(top.shape[0], bottom_flipped.shape[0])
    vert_diff = np.logical_xor(top[-min_h:, :], bottom_flipped[:min_h, :]).sum()

    total_area = max(mask.sum() / 255, 1)
    return float((horiz_diff + vert_diff) / (2 * total_area))


def _border_compactness(mask):
    """Compactness = perimeter^2 / (4*pi*area). 1.0 = perfect circle,
    higher values indicate an irregular border (melanoma warning sign)."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return 1.0
    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    if area <= 0:
        return 1.0
    return float((perimeter ** 2) / (4 * np.pi * area))


def _color_stats(img_bgr, mask):
    lesion_pixels_bgr = img_bgr[mask > 0]
    if lesion_pixels_bgr.size == 0:
        return [0.0] * 6, 1
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lesion_pixels_hsv = hsv[mask > 0]

    std_bgr = lesion_pixels_bgr.std(axis=0).tolist()
    std_hsv = lesion_pixels_hsv.std(axis=0).tolist()

    # crude color-cluster count via k-means, as a proxy for "color variegation"
    from sklearn.cluster import KMeans
    sample = lesion_pixels_bgr[:: max(1, len(lesion_pixels_bgr) // 500)]
    best_k, best_score = 1, None
    for k in range(1, 4):
        if len(sample) < k:
            break
        km = KMeans(n_clusters=k, n_init=3, random_state=0).fit(sample)
        inertia = km.inertia_
        if best_score is None or inertia < best_score * 0.7:
            best_k, best_score = k, inertia
    return std_bgr + std_hsv, best_k


def _diameter_and_area(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0, 0.0
    c = max(contours, key=cv2.contourArea)
    (_, _), radius = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    return float(2 * radius), float(area)


def _glcm_features(img_bgr, mask):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray_masked = gray.copy()
    gray_masked[mask == 0] = 0
    glcm = graycomatrix(gray_masked, distances=[1], angles=[0], levels=256,
                         symmetric=True, normed=True)
    contrast = graycoprops(glcm, "contrast")[0, 0]
    homogeneity = graycoprops(glcm, "homogeneity")[0, 0]
    energy = graycoprops(glcm, "energy")[0, 0]
    correlation = graycoprops(glcm, "correlation")[0, 0]
    return [float(contrast), float(homogeneity), float(energy), float(correlation)]


def extract_handcrafted_features(img_bgr, mask):
    """Returns a fixed-length feature vector (see FEATURE_NAMES) for one lesion."""
    asymmetry = _asymmetry_score(mask)
    compactness = _border_compactness(mask)
    color_std, n_clusters = _color_stats(img_bgr, mask)
    diameter, area = _diameter_and_area(mask)
    glcm = _glcm_features(img_bgr, mask)

    features = [asymmetry, compactness] + color_std + [float(n_clusters), diameter, area] + glcm
    return np.array(features, dtype=np.float32)
