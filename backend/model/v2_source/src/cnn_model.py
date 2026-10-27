"""
cnn_model.py
------------
The deep-learning branch of the hybrid model.

Architecture: a compact CNN (Conv-BN-ReLU-Pool x3 -> GlobalAveragePooling
-> Dense(64) -> Dense(1, sigmoid)), chosen so it is cheap enough to run
without a GPU or pretrained ImageNet weights (this sandbox cannot reach
external weight-hosting servers). In a real deployment with internet
access, swap `build_cnn()` for a MobileNetV3Small/EfficientNet-Lite
transfer-learning backbone (see README "Swapping in a pretrained
backbone") -- the rest of the pipeline (feature fusion, classical
classifier, stratified evaluation) does not need to change.

After training, `extract_deep_features()` returns the activations of the
Dense(64) layer for each image -- this is the CNN's contribution to the
fused feature vector used by the classical classifier.
"""
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models


def build_cnn(input_shape=(128, 128, 3)):
    inputs = layers.Input(shape=input_shape)
    x = layers.Rescaling(1.0 / 255)(inputs)

    for filters in (16, 32, 64):
        x = layers.Conv2D(filters, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)
        x = layers.MaxPooling2D()(x)

    x = layers.GlobalAveragePooling2D()(x)
    feat = layers.Dense(64, activation="relu", name="deep_features")(x)
    x = layers.Dropout(0.3)(feat)
    outputs = layers.Dense(1, activation="sigmoid", name="cnn_head")(x)

    model = models.Model(inputs, outputs, name="melanoma_cnn_branch")
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
                  loss="binary_crossentropy",
                  metrics=["accuracy", tf.keras.metrics.AUC(name="auc")])
    return model


def build_cnn_multiclass(input_shape=(128, 128, 3), num_classes=5):
    """Same compact CNN backbone as build_cnn(), but with a softmax head for
    the 5-class real-data risk categories instead of the binary sigmoid head
    used on the synthetic benign/melanoma demo. The 'deep_features' layer
    keeps the same name so cnn_model.get_feature_extractor() works unchanged
    for either variant."""
    inputs = layers.Input(shape=input_shape)
    x = layers.Rescaling(1.0 / 255)(inputs)

    for filters in (16, 32, 64):
        x = layers.Conv2D(filters, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)
        x = layers.MaxPooling2D()(x)

    x = layers.GlobalAveragePooling2D()(x)
    feat = layers.Dense(64, activation="relu", name="deep_features")(x)
    x = layers.Dropout(0.3)(feat)
    outputs = layers.Dense(num_classes, activation="softmax", name="cnn_head")(x)

    model = models.Model(inputs, outputs, name="risk_cnn_branch_multiclass")
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    return model


def build_cnn_multiclass_pretrained(input_shape=(128, 128, 3), num_classes=5,
                                     fine_tune=False, fine_tune_layers=30):
    """Transfer-learning variant of build_cnn_multiclass(): MobileNetV2
    backbone pretrained on ImageNet (frozen by default) instead of a tiny
    from-scratch CNN. This is the single biggest lever for real-data
    accuracy, since ~1000 images/class from scratch is not enough signal
    for a CNN to learn good features on its own.

    Needs internet access to download ImageNet weights the first time
    (works in Colab; NOT available in an offline sandbox). The
    'deep_features' layer keeps the same name so get_feature_extractor()
    works unchanged for either variant.

    fine_tune=True unfreezes the last `fine_tune_layers` backbone layers
    for a further accuracy bump -- do this only AFTER a few epochs of
    head-only training (fine_tune=False first), since fine-tuning an
    untrained head from the start tends to destroy the pretrained weights."""
    base = tf.keras.applications.MobileNetV2(
        input_shape=input_shape, include_top=False, weights="imagenet", pooling="avg"
    )
    base.trainable = False
    if fine_tune:
        base.trainable = True
        for layer in base.layers[:-fine_tune_layers]:
            layer.trainable = False

    inputs = layers.Input(shape=input_shape)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
    x = base(x, training=False)
    feat = layers.Dense(64, activation="relu", name="deep_features")(x)
    x = layers.Dropout(0.3)(feat)
    outputs = layers.Dense(num_classes, activation="softmax", name="cnn_head")(x)

    model = models.Model(inputs, outputs, name="risk_cnn_branch_pretrained")
    lr = 1e-4 if fine_tune else 1e-3
    model.compile(optimizer=tf.keras.optimizers.Adam(lr),
                  loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def train_cnn(model, X_train, y_train, X_val, y_val, epochs=15, batch_size=16,
              class_weight=None, monitor="val_auc", mode="max"):
    """class_weight lets the (heavily imbalanced) real-data multiclass CNN
    down-weight the majority class instead of just predicting it every time.
    monitor/mode default to the binary demo's val_auc; pass monitor='val_loss',
    mode='min' for the multiclass head (no per-class AUC metric is attached)."""
    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor=monitor, mode=mode, patience=4, restore_best_weights=True
    )
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop],
        class_weight=class_weight,
        verbose=2,
    )
    return history


def get_feature_extractor(trained_model):
    """Returns a sub-model that outputs the Dense(64) 'deep_features' layer."""
    return models.Model(
        inputs=trained_model.input,
        outputs=trained_model.get_layer("deep_features").output,
    )


def extract_deep_features(feature_extractor, X, batch_size=32):
    return feature_extractor.predict(X, batch_size=batch_size, verbose=0)
