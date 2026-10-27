"""
segmentation.py
----------------
Step 3 of the methodology: isolate the lesion region from surrounding
healthy skin using Otsu thresholding + morphological cleanup, and keep
only the largest connected component (the assumed lesion).
"""
import cv2
import numpy as np


def segment_lesion(img_bgr):
    """
    Returns:
        mask (H,W) uint8, 255 = lesion, 0 = background
        masked_img (H,W,3) the original image with background zeroed out
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Otsu threshold. Lesions are typically darker than surrounding skin,
    # so we take the inverse if the foreground would otherwise be the
    # (larger) background region.
    _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # If more than half the image got marked foreground, thresholding
    # likely picked the skin instead of the lesion -> invert.
    if np.mean(mask > 0) > 0.5:
        mask = cv2.bitwise_not(mask)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    clean_mask = np.zeros_like(mask)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        cv2.drawContours(clean_mask, [largest], -1, 255, -1)
    else:
        clean_mask = mask  # fallback

    masked_img = cv2.bitwise_and(img_bgr, img_bgr, mask=clean_mask)
    return clean_mask, masked_img
