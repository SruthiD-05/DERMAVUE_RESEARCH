# V2 inference contract (prepared, not enabled)

This is the serving contract to implement only after a genuine-data evaluation
gate passes. The current backend deliberately returns `503 model_unavailable`.

## Input

`POST /api/cases/{case_id}/analyze`

- Content type: `multipart/form-data`.
- Required field: one or more `images` containing JPEG, PNG, or WebP image data.
- Required field for each image: matching `image_ids` value from the case record.
- The case must contain a dermoscopic image and the image must be readable.
- Clinical images may be stored as context, but must not be silently passed to a
  model that was evaluated on dermoscopic images only.
- The final adapter must enforce configured maximum size, decoded dimensions,
  MIME type, and image count before preprocessing.

## Preprocessing and task

The adapter must load the exact versioned bundle used for the final evaluation:

1. image decoding and the V2 preprocessing configuration;
2. lesion segmentation configuration;
3. CNN feature extractor checkpoint;
4. handcrafted ABCD/texture feature extraction;
5. fitted metadata transformer, when the selected task uses metadata;
6. fitted feature scaler and classical classifier;
7. ordered label mapping.

The current real-data source defines a five-class mapping in
`backend/model/v2_source/src/metadata_features.py`. A binary model is a
different contract and must be versioned separately. The adapter must reject a
bundle whose task, label mapping, preprocessing hash, or artifact checksums do
not match the evaluated report.

## Successful response

```json
{
  "predictedLabel": "<label from the evaluated mapping>",
  "scores": [{"label": "<label>", "score": 0.0}],
  "scoresAreCalibrated": false,
  "riskCategory": "<research risk category>",
  "modelName": "Melanoma Hybrid V2",
  "modelVersion": "<validated bundle version>",
  "inputImageId": "<case image id>",
  "inferredAt": "<ISO-8601 timestamp>",
  "analysisStatus": "complete",
  "explanationAvailable": false
}
```

Scores must be actual outputs from the loaded artifact. If calibration was not
validated, `scoresAreCalibrated` must remain false. The response is research
output, not a diagnosis.

## Required failures

- `400 invalid_input`: missing images, unsupported MIME type, malformed image,
  missing image ID, or incompatible case inputs.
- `404 not_found`: case or image ID does not exist.
- `503 model_unavailable`: checkpoint, preprocessing bundle, evaluation proof,
  or compatible serving configuration is missing.
- `500 inference_failed`: a validated bundle failed during inference; include a
  safe error identifier, not a prediction or fabricated fallback.

The backend must continue returning `503 model_unavailable` until the checklist
evaluation and artifact gates are complete.
