# Genuine dataset acquisition plan

The official HAM10000 Dataverse release (version 4) has been downloaded and
verified under `data/raw/ham10000/`, with extracted derivatives under
`data/processed/ham10000/`. Its provenance, terms, checksums, validation
counts, and baseline result are recorded in
`data/reports/ham10000_acquisition.md`. The existing synthetic data remains
under its original experiment directories.

The official ISIC 2020 ground-truth, duplicate-list, and JPEG archive have
been placed under `data/raw/isic2020/` from the official ISIC S3 release. The
archive is complete, SHA-256 verified, and extracted into a separate images
directory. It is a frozen candidate external-evaluation source, not an
independent validation result. MRA-MIDAS, BCN20000, Derm7pt, and
PAD-UFES-20 remain separate acquisition or compatibility investigations; none
may be pooled or presented as external validation until their official access
terms, labels, grouping identifiers, and overlap status are verified. The
current source audit is recorded in
`data/reports/external_dataset_access_audit.md` and the phase-specific plan in
`docs/research_protocol/external_dataset_acquisition_plan.md`.

## Candidate inventory

| Candidate | Best use in DermaVue research | Main compatibility issue | Acquisition gate |
|---|---|---|---|
| HAM10000 | Primary baseline for the existing five-class real-data pipeline | Dermoscopic only; `lesion_id` is available but patient identifiers are not in the supplied metadata; seven labels are collapsed into five categories | **Acquired and verified.** Baseline is 0.7603 accuracy and remains non-serving. |
| ISIC challenge releases | Large dermoscopic baseline or external source, depending on release | Labels, licenses, metadata, and test-label availability differ by release; cross-release overlap must be checked | Select a specific release, not “ISIC” generically; record official manifest and terms |
| BCN20000 | Strong external dermoscopic source and source-shift/OOD study | Class taxonomy differs from V2; official test labels and the OOD class require careful handling | Obtain the training metadata and permitted evaluation material; do not treat unknown test cases as ordinary five-class labels |
| Derm7pt | Paired clinical + dermoscopic reliability experiments | Small (1,011 cases), different diagnosis and seven-point label schema | Verify access terms and create a separate label contract; never force all labels into HAM10000 categories without review |
| PAD-UFES-20 | Clinical-image external robustness/domain study | Smartphone clinical images and a different diagnosis schema; not drop-in dermoscopic training data | Obtain official data and label documentation; use only with a declared modality/task mapping |
| MRA-MIDAS | Highest-priority investigation for paired prospective multimodal data | Access, license, exact release and label schema require direct verification | Visit official Stanford AIMI page, request/download under terms, record DOI/checksum and IRB/provenance details |
| PH2 | Small sanity/external test set | Very small and limited classes; insufficient for the primary training target | Use only as a declared external or qualitative benchmark if permitted |
| MED-NODE | Small clinical external sanity check | 170 images and binary clinical task; weak for training a five-class model | Use only as a separately declared external test if terms permit |

## Manual actions required

1. Obtain remaining dataset releases through their official portals. Some sources may
   require registration, an account, or acceptance of terms that cannot be
   completed by the local preparation scripts.
2. Save license/terms, citation, source URL, release date, and checksums
   under `data/reports/provenance/` before extracting any files.
3. Place immutable archives under `data/raw/<source>/`; do not overwrite a
   previously verified archive.
4. Extract into source-specific directories and run the V2 preparation command
   only after verifying image IDs and metadata columns.
5. Generate manifests under `data/manifests/<source>/<version>/` and inspect
   class, lesion, patient, source, and duplicate reports before training.

## Dataset selection rule

The primary training dataset must match the declared V2 input modality and label
contract. A larger dataset is not automatically better if it lacks reliable
labels, stable lesion/patient grouping, or compatible modality. External data
must remain source-identifiable and must not be pooled into the internal test
set.
