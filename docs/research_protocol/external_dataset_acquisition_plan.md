# External dataset acquisition plan

Status date: 2026-10-01. This plan distinguishes source facts, acquired
artifacts, and unresolved access or independence questions.

## Priority decisions

1. **ISIC 2020** is the first public acquisition candidate. The official
   portal provides a versioned JPEG release, ground truth, patient metadata,
   and a duplicate-image list under the release's CC-BY-NC terms. Its archive
   and source files are now acquired, verified, and audited as a separate
   evaluation task, not pooled with HAM10000.
2. **MRA-MIDAS** remains the best candidate for paired clinical/dermoscopic
   reliability analysis. The official Stanford page links to a Redivis
   subscription dataset; no credentials or institutional authorization are
   available in this workspace, so access is not bypassed.
3. **BCN20000** is a strong dermoscopic source and is publicly described as
   CC-BY 4.0, but its direct source archive was not acquired in this phase.
   The ISIC 2019 aggregate must not be substituted without source-level overlap
   auditing because it combines BCN20000, HAM10000, and MSK data.
4. **PAD-UFES-20** and **Derm7pt** remain modality/task candidates. PAD-UFES-20
   is smartphone clinical photography; Derm7pt is paired but access terms and
   the original release contract still require direct confirmation.

## Acquisition record requirements

For each source, preserve the original archive and record:

- official URL, citation, release/version date, and access date;
- license/terms and whether research use is non-commercial or restricted;
- archive and metadata SHA-256 checksums;
- image and case counts from the source and local files;
- schema, label mapping, patient/lesion identifiers, modality, and missingness;
- official duplicate lists and exact/perceptual overlap reports;
- the decision to use, exclude, or defer the source.

No dataset may be pooled with HAM10000 merely because its name appears in an
ISIC challenge aggregate. Source identity and overlap must be explicit.

## Next legitimate access actions

- Preserve the completed ISIC 2020 archive and acquisition manifest; do not
  restart or overwrite the download.
- Re-run extraction only into a new versioned derivative directory if a future
  reproducibility check is needed; do not modify the original archive.
- Re-run the external manifest validator and DCT overlap audit only into a new
  versioned output directory/report; the current frozen candidate is recorded
  under `data/manifests/isic2020_binary_melanoma_v1_external_eval/`.
- For MRA-MIDAS, obtain the required Stanford/Redivis subscription or
  institutional authorization through the dataset owner; do not use mirrors
  or scrape around access controls.
- For BCN20000, obtain the original Figshare release and its terms directly,
  then audit it as a source-specific cohort rather than using the ISIC 2019
  aggregate.
