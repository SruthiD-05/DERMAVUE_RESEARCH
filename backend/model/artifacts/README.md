# V2 serving artifact directory

This directory is intentionally empty except for this safety note. Do not copy
the synthetic demo checkpoint or fusion classifier here.

When a genuine-data model passes the evaluation gates, the serving bundle must
include the exact evaluated CNN checkpoint, fusion classifier, fitted scaler,
metadata pipeline, label mapping, preprocessing configuration, and a
`release_manifest.json` with at least:

```json
{
  "data_provenance": "genuine",
  "evaluation_gate_passed": true,
  "task": "ham10000_five_class",
  "model_version": "<immutable version>",
  "test_manifest_sha256": "<checksum>",
  "artifact_sha256": {
    "cnn_branch.keras": "<checksum>"
  }
}
```

The current adapter still reports inference as unavailable even when an
artifact is present until the serving implementation is verified for exact
preprocessing, label mapping, input validation, and checkpoint parity.
