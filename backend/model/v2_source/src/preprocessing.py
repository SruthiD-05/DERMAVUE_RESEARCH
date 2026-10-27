"""
preprocessing.py
-----------------
Step 2 of the methodology: noise removal, hair-artifact removal, and
normalization, applied before segmentation and feature extraction.

Hair removal uses the standard "DullRazor-style" approach used widely in
dermoscopy pipelines: a blackhat morphological filter isolates thin dark
structures (hairs), a mask is built by thresholding that response, and the
hair pixels are removed via inpainting.
"""
import cv2
import numpy as np


def remove_hair(img_bgr, kernel_size=9, thresh=10):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    _, hair_mask = cv2.threshold(blackhat, thresh, 255, cv2.THRESH_BINARY)
    inpainted = cv2.inpaint(img_bgr, hair_mask, 3, cv2.INPAINT_TELEA)
    return inpainted


def denoise(img_bgr):
    return cv2.fastNlMeansDenoisingColored(img_bgr, None, 5, 5, 7, 21)


def resize_normalize(img_bgr, size=128):
    resized = cv2.resize(img_bgr, (size, size), interpolation=cv2.INTER_AREA)
    return resized


def preprocess_image(path_or_array, size=128, do_hair_removal=True, do_denoise=False):
    """Full Step-2 preprocessing pipeline. Accepts a file path or a BGR ndarray."""
    if isinstance(path_or_array, str):
        img = cv2.imread(path_or_array)
        if img is None:
            raise FileNotFoundError(path_or_array)
    else:
        img = path_or_array.copy()

    img = resize_normalize(img, size=size)
    if do_hair_removal:
        img = remove_hair(img)
    if do_denoise:
        img = denoise(img)
    return img
