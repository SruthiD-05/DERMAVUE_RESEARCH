# Binary operating-point protocol

Protocol version: `binary_melanoma_other_dx_v1_threshold_analysis`  
Model: frozen Random Forest fusion bundle from
`experiments/binary_melanoma/v1_mobilenetv2_fusion_seed42/`  
Selection data: binary validation manifest only  
Test data: binary test manifest, scored once after threshold selection

## Prespecified rule

Evaluate the fixed threshold grid `0.10, 0.15, ..., 0.90`. Select the lowest
threshold that maximizes melanoma sensitivity subject to validation specificity
being at least `0.75`. Ties are resolved by higher specificity, then the lower
threshold. The original fixed threshold `0.50` remains the baseline. No test
labels, test probabilities, or five-class test results enter this selection.

The threshold is an exploratory research operating point, not a clinical safety
threshold. Bootstrap intervals resample lesion groups where possible because
patient IDs are unavailable.
