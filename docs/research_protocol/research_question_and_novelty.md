# Research question and novelty gate

Status: protocol draft; no method is approved as novel.

## Search record

- Search date: 2026-10-01.
- Sources consulted: official ISIC and dataset pages, PubMed, publisher pages,
  NeurIPS proceedings, PMC, and recent peer-reviewed/preprint search results.
- Search concepts: `skin lesion multimodal clinical dermoscopic fusion`, `skin
  lesion image quality`, `dermoscopy calibration abstention selective
  classification`, `skin lesion domain shift external validation`, `Derm7pt`,
  `HAM10000`, `BCN20000`, `PAD-UFES-20`.
- Inclusion focus: genuine skin-lesion image studies or datasets, paired or
  metadata-aware methods, reliability/quality/abstention, and reporting
  guidance relevant to medical imaging AI.
- Exclusion focus: synthetic-only experiments as evidence, papers without
  identifiable sources, non-skin-image work used only as background, and
  claims that could not be checked from a primary or official source.
- This is an initial focused review, not yet a registered systematic review.
  A full publication search should add PubMed, IEEE Xplore, Scopus/Web of
  Science, and backward/forward citation screening before manuscript submission.

## Candidate contributions

| Candidate | Literature status | Feasibility | Decision |
|---|---|---|---|
| Quality-conditioned multimodal fusion | Quality effects and multimodal fusion are established; quality-conditioned fusion may still be a useful combination | Requires quality labels or defensible quality proxies plus paired modalities | Keep as a hypothesis, not a novelty claim |
| Cross-modal disagreement as an error/reliability signal | Missing-modality and multimodal fusion are established; explicit disagreement-to-error analysis is less directly covered in the reviewed set | Requires verified clinical/dermoscopic pairs and calibrated modality-specific predictions | Primary candidate for investigation |
| Reliability-aware selective prediction under quality and missing modality | Selective classification and abstention are established generally; dermatology-specific source-separated evaluation is the measurable opportunity | Feasible with any labeled image data; paired data improves the question | Primary evaluation contribution, not claimed algorithmic novelty |
| New attention/fusion architecture | Closely related attention and adversarial fusion methods already exist | Easy to implement but weak novelty and high overfitting risk | Reject as the paper's sole contribution |

## Bounded research question

> On genuinely paired skin-lesion cases, does adding image-quality indicators
> and cross-modal disagreement to a calibrated multimodal V2 baseline improve
> selective risk-coverage behavior and robustness to missing or degraded
> modalities, without degrading melanoma sensitivity, under lesion/patient-safe
> internal testing and source-separated external testing?

This question is deliberately conditional. If the acquired data does not
contain verified pairs, the paired component will be removed and the study will
be reframed as quality-aware selective prediction for single-modality data.

## Planned comparisons

1. Existing V2 five-class baseline.
2. MobileNetV2-compatible V2 image branch.
3. Standard metadata/image late fusion.
4. Quality-only weighting.
5. Disagreement-only weighting on verified pairs.
6. Reliability-aware selective prediction.
7. Ablations removing quality, disagreement, and abstention components.
8. Unmodified internal test, controlled corruption tests, and source-separated
   external test where the label contract is compatible.

## Novelty and claim guardrails

- Do not claim “first,” “novel,” or “clinically safe.”
- Describe any contribution as an empirical framework or evaluation study until
  literature screening and ablations demonstrate a distinct, reproducible
  method.
- Treat an abstention output as “requires review,” never as a diagnosis or a
  safety guarantee.
- A 90% accuracy result, if achieved, does not establish clinical validation or
  generalization.
