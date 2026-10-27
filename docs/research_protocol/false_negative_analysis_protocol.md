# Binary false-negative analysis protocol

Protocol version: `binary_melanoma_other_dx_v1_fn_analysis`  
Input: frozen binary test predictions and test manifest only  
Purpose: post-hoc error characterization, not model selection

The analysis describes all 77 melanoma false negatives at the fixed 0.5
operating point. It records predicted probability, confidence, original `dx`,
available age/sex/localization metadata, and genuine-image quality proxies.
No threshold, feature, model, or training decision is made from these test
outcomes. Confidence-coverage summaries are descriptive and are not clinical
operating recommendations.

Uncertainty for the melanoma false-negative rate is estimated with a grouped
bootstrap resampling `lesion_id` where available. Patient-level or skin-tone
effects are not inferred because patient IDs and ground-truth skin-tone labels
are absent.
