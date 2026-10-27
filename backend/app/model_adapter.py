from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .partner_adapter import PartnerModelAdapter


@dataclass(frozen=True)
class ModelStatus:
    name: str | None = None
    version: str | None = None
    checkpoint_loaded: bool = False
    inference_available: bool = False
    state: str = "configuration-required"
    artifact_state: str = "missing"
    load_state: str = "not-loaded"
    release_state: str = "not-approved"
    architecture: str | None = None
    metadata_source: str | None = None
    reported_metrics: dict | None = None
    research_mode: bool = False
    message: str = "No inference model is configured."


class V2ModelAdapter:
    """Safe adapter boundary for the supplied V2 implementation.

    The adapter intentionally refuses to produce predictions until a genuine
    checkpoint is placed in the configured artifact directory, its evaluation
    gate is approved, and an inference implementation is verified against the
    original preprocessing and labels.
    """

    def __init__(self, artifact_dir: Path | None = None) -> None:
        self.artifact_dir = artifact_dir or Path(__file__).resolve().parents[1] / "model" / "artifacts"
        self.partner_dir = self.artifact_dir / "teammate_partner_v1"
        self.partner = PartnerModelAdapter(self.partner_dir)

    @staticmethod
    def research_enabled() -> bool:
        return os.environ.get("DERMAVUE_RESEARCH_INFERENCE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}

    def load_research_model(self) -> None:
        if not self.research_enabled():
            raise RuntimeError("Local research inference is disabled.")
        self.partner.load_for_research()

    def status(self) -> ModelStatus:
        # The partner bundle is intentionally present but release-disabled.
        # Do not infer serving readiness merely from large checkpoint files.
        if self.partner_dir.exists():
            try:
                manifest = json.loads((self.partner_dir / "release_manifest.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                manifest = {}
            try:
                self.partner.verify_artifacts(manifest)
            except Exception as exc:
                return ModelStatus(state="artifacts-invalid", artifact_state="invalid", release_state="blocked", message=f"Partner model artifacts are present but invalid: {exc}")
            metadata = self._partner_metadata(manifest)
            if self.research_enabled():
                if self.partner._model is not None:
                    return ModelStatus(**metadata, checkpoint_loaded=True, inference_available=True, state="research-available", artifact_state="installed", load_state="loaded", release_state="serving-disabled", research_mode=True, message="Local research inference is enabled and the verified partner model is loaded. Production serving remains disabled.")
                return ModelStatus(**metadata, state="research-enabled-not-loaded", artifact_state="installed", load_state="not-loaded", release_state="serving-disabled", research_mode=True, message="Local research inference is enabled but the partner model is not loaded yet.")
            if manifest.get("evaluation_gate_passed") is True and manifest.get("serving_enabled") is True:
                try:
                    self.partner.verify_release()
                except Exception as exc:
                    return ModelStatus(**metadata, state="release-approved", artifact_state="installed", load_state="not-loaded", release_state="approved-but-not-loaded", message=str(exc))
                return ModelStatus(**metadata, checkpoint_loaded=True, inference_available=True, state="connected", artifact_state="installed", load_state="loaded", release_state="serving", message="Verified partner model is loaded and approved for inference.")
            return ModelStatus(**metadata, state="release-disabled", artifact_state="installed", load_state="not-loaded", release_state="serving-disabled", message="Model installed — serving disabled: the genuine-data release decision is not approved; model_unavailable remains enforced.")
        weights = tuple(self.artifact_dir.glob("*.h5")) + tuple(self.artifact_dir.glob("*.keras")) + tuple(self.artifact_dir.glob("*.ckpt*"))
        if weights:
            release_manifest = self.artifact_dir / "release_manifest.json"
            if not release_manifest.exists():
                return ModelStatus(state="artifacts-present", artifact_state="installed", load_state="not-loaded", release_state="not-approved", message="Model artifacts are present but no release manifest is approved; inference remains disabled.")
            try:
                manifest = json.loads(release_manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                manifest = {}
            if manifest.get("data_provenance") != "genuine" or manifest.get("evaluation_gate_passed") is not True:
                return ModelStatus(state="release-disabled", artifact_state="installed", load_state="not-loaded", release_state="serving-disabled", message="Model artifacts are installed, but release approval is disabled; inference remains unavailable.")
            return ModelStatus(state="artifacts-present", artifact_state="installed", load_state="not-loaded", release_state="approved-but-not-loaded", message="A genuine-data artifact is present, but the serving adapter has not been verified against the evaluated bundle.")
        return ModelStatus()

    @staticmethod
    def _partner_metadata(manifest: dict) -> dict:
        return {
            "name": "Partner tri-modal melanoma hybrid",
            "version": manifest.get("model_version", "teammate_partner_v1"),
            "architecture": "Three CNN streams (EffNet-B4, EffNetV2-S, EffNet-B4 seed 7) + ABCD/texture and metadata XGBoost fusion",
            "metadata_source": "hash-verified partner release manifest and configuration",
            "reported_metrics": {
                "rawImageAccuracy": {"value": manifest.get("raw_image_accuracy"), "label": "Unverified research-package raw image-score accuracy"},
                "rawImageRocAuc": {"value": manifest.get("raw_image_roc_auc"), "label": "Unverified research-package raw image-score AUROC"},
                "lesionLevelAccuracy": {"value": manifest.get("lesion_level_accuracy"), "label": "Unverified research-package lesion-level accuracy"},
                "lesionLevelRocAuc": {"value": manifest.get("lesion_level_roc_auc"), "label": "Unverified research-package lesion-level AUROC"},
            },
        }

    def info(self) -> dict:
        if self.partner_dir.exists():
            try:
                manifest = json.loads((self.partner_dir / "release_manifest.json").read_text(encoding="utf-8"))
                self.partner.verify_artifacts(manifest)
                metadata = self._partner_metadata(manifest)
                metadata["metadataSource"] = metadata.pop("metadata_source")
                return {
                    **metadata,
                    "supportedInputs": ["clinical", "dermoscopic"],
                    "allowedLocalizations": self.partner.allowed_localizations(),
                    "sexValues": ["male", "female", "unknown"],
                    "outputCategories": ["BENIGN", "MALIGNANT"],
                    "returnsProbabilities": False,
                    "diagnosisLevel": "binary",
                    "subtypeAvailable": False,
                    "auxiliaryOutputCategories": ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"],
                    "returnsAuxiliaryClassScores": True,
                    "scoreSemantics": "Final fused malignancy score is binary; auxiliary class scores are the mean of the three CNN seven-class softmax outputs and are not calibrated probabilities or validated subtype predictions.",
                    "evaluation": {"dataset": "Partner-supplied genuine research package", "limitations": ["Patient-level independence and duplicate leakage remain unresolved", "Not clinical validation", "Release serving is disabled"]},
                    "verification": {"artifactHashesVerified": True, "evaluationGatePassed": False, "servingEnabled": False},
                }
            except Exception:
                return {"verification": {"artifactHashesVerified": False}, "message": "Partner artifact metadata is unavailable because integrity verification failed."}
        return {
            "verification": {"artifactHashesVerified": False},
            "supportedInputs": ["clinical", "dermoscopic"],
            "message": "No verified model artifacts are configured.",
        }

    def predict(self, _payload: object) -> dict:
        raise RuntimeError(self.status().message)
