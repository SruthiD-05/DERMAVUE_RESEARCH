"""
dataset.py
----------
Loads images from a directory structured as:
    root/<class_name>/<skin_tone_group>/*.jpg

`class_name` is expected to be "benign" or "melanoma" (binary task, matching
the ISIC melanoma-detection framing). `skin_tone_group` is a free-form label
(e.g. "light"/"medium"/"dark", or Fitzpatrick I-VI) used ONLY for stratified
evaluation later -- it is never given to the model as an input feature,
since the model should not use skin tone to predict the label.
"""
import os
import glob
import numpy as np
from preprocessing import preprocess_image
from segmentation import segment_lesion

CLASS_TO_LABEL = {"benign": 0, "melanoma": 1}


def load_dataset(root_dir, img_size=128):
    images, masks, labels, skin_tones, paths = [], [], [], [], []

    for cls_name, label in CLASS_TO_LABEL.items():
        cls_dir = os.path.join(root_dir, cls_name)
        if not os.path.isdir(cls_dir):
            continue
        for tone_name in sorted(os.listdir(cls_dir)):
            tone_dir = os.path.join(cls_dir, tone_name)
            if not os.path.isdir(tone_dir):
                continue
            for fpath in sorted(glob.glob(os.path.join(tone_dir, "*.jpg"))):
                img = preprocess_image(fpath, size=img_size)
                mask, _ = segment_lesion(img)
                images.append(img)
                masks.append(mask)
                labels.append(label)
                skin_tones.append(tone_name)
                paths.append(fpath)

    return (
        np.array(images, dtype=np.uint8),
        masks,  # list of (H,W) uint8 arrays, kept as a list (masks can vary)
        np.array(labels, dtype=np.int32),
        np.array(skin_tones),
        np.array(paths),
    )
