# Supplied V2 model integration

The exact source files from `melanoma_hybrid_v2.zip` are preserved in `v2_source/`.

The archive contains TensorFlow model/training source, a synthetic demo dataset,
and output summaries, but no trained checkpoint or production inference API.
Therefore the active adapter reports the model as unavailable and returns HTTP 503
for analysis requests. This is intentional: the application never fabricates a
prediction, confidence, probability, or explainability output.

When a verified checkpoint and inference contract are supplied, implement and
test the adapter in `backend/app/model_adapter.py` against the original source
preprocessing, label mapping, and input requirements before enabling inference.
