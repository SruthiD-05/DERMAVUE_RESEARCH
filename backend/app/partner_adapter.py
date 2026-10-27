from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class PartnerAdapterError(RuntimeError):
    pass


class PartnerModelUnavailable(PartnerAdapterError):
    pass


class PartnerInvalidInput(PartnerAdapterError):
    pass


class PartnerInferenceError(PartnerAdapterError):
    pass


class PartnerModelAdapter:
    """Compatibility boundary for the audited partner package.

    Loading is deliberately lazy and requires both release flags in the
    immutable-in-practice manifest. The supplied audit leaves those flags off.
    """

    required = ("config.json", "EffNet-B4.keras", "EffNet-B4-s7.keras", "EffNetV2-S.keras", "xgb_tabular.json")

    def __init__(self, bundle_dir: Path):
        self.bundle_dir = bundle_dir
        self._model: Any = None

    def _manifest(self) -> dict[str, Any]:
        try:
            return json.loads((self.bundle_dir / "release_manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PartnerModelUnavailable("Partner release manifest is missing or invalid.") from exc

    def verify_release(self) -> dict[str, Any]:
        manifest = self._manifest()
        if manifest.get("data_provenance") != "genuine" or manifest.get("evaluation_gate_passed") is not True or manifest.get("serving_enabled") is not True:
            raise PartnerModelUnavailable("Partner model is installed but its genuine-data release gate is not approved.")
        return self.verify_artifacts(manifest)

    def verify_artifacts(self, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
        manifest = manifest or self._manifest()
        for filename in self.required:
            path = self.bundle_dir / filename
            if not path.is_file():
                raise PartnerModelUnavailable(f"Required partner artifact is missing: {filename}")
            expected = manifest.get("artifacts", {}).get(filename)
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise PartnerModelUnavailable(f"Partner artifact hash mismatch: {filename}")
        return manifest

    def allowed_localizations(self) -> list[str]:
        try:
            config = json.loads((self.bundle_dir / "config.json").read_text(encoding="utf-8"))
            return [str(value) for value in config.get("LOCS", [])]
        except (OSError, ValueError, TypeError):
            return []

    def _load(self, *, research_mode: bool = False) -> Any:
        if research_mode:
            self.verify_artifacts()
        else:
            self.verify_release()
        if self._model is None:
            source = self.bundle_dir / "partner_inference.py"
            spec = importlib.util.spec_from_file_location("dermavue_partner_inference", source)
            if spec is None or spec.loader is None:
                raise PartnerModelUnavailable("Partner inference source cannot be loaded.")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._model = module.SkinCancerModel(str(self.bundle_dir), tta_views=8)
        return self._model

    def load_for_research(self) -> Any:
        return self._load(research_mode=True)

    @staticmethod
    def _score(value: Any, field: str) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError) as exc:
            raise PartnerInferenceError(f"Partner response contains an invalid {field}.") from exc
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise PartnerInferenceError(f"Partner response contains an out-of-range {field}.")
        return score

    def predict(self, images: list[bytes], image_ids: list[str], *, age: float | None, sex: str, localization: str, research_mode: bool = False) -> dict[str, Any]:
        if not images or len(images) != len(image_ids):
            raise PartnerInvalidInput("At least one image and a matching image_id are required.")
        if len(images) > 4:
            raise PartnerInvalidInput("A maximum of four images may be analyzed per request.")
        if sex not in {"male", "female", "unknown"}:
            raise PartnerInvalidInput("sex must be male, female, or unknown.")
        if localization not in self.allowed_localizations():
            raise PartnerInvalidInput(f"Unknown localization '{localization}'.")
        decoded: list[np.ndarray] = []
        for image in images:
            bgr = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
            if bgr is None:
                raise PartnerInvalidInput("Could not decode an image. Send a JPG, JPEG, or PNG image.")
            decoded.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        try:
            result = self._load(research_mode=research_mode).predict(decoded, age=age, sex=sex, localization=localization)
        except PartnerAdapterError:
            raise
        except Exception as exc:
            raise PartnerInferenceError("Partner inference failed.") from exc
        prediction = str(result.get("prediction", ""))
        risk = str(result.get("risk_level", ""))
        if prediction not in {"BENIGN", "MALIGNANT"} or risk not in {"LOW", "MODERATE", "HIGH"}:
            raise PartnerInferenceError("Partner response contains an unsupported prediction or risk category.")
        score = self._score(result.get("malignancy_score"), "malignancy_score")
        stream_scores = {key: self._score(value, key) for key, value in (result.get("stream_scores") or {}).items()}
        auxiliary_scores_raw = result.get("auxiliary_class_scores") or {}
        if not isinstance(auxiliary_scores_raw, dict):
            raise PartnerInferenceError("Partner response contains invalid auxiliary class scores.")
        class_scores = [{"label": str(key), "score": self._score(value, f"auxiliary_class_scores.{key}")} for key, value in auxiliary_scores_raw.items()]
        if class_scores and len(class_scores) != 7:
            raise PartnerInferenceError("Partner response contains an incomplete auxiliary class score set.")
        thresholds = result.get("thresholds") or {}
        if any(self._score(value, f"thresholds.{key}") > 1 for key, value in thresholds.items()):
            raise PartnerInferenceError("Partner response contains invalid thresholds.")
        disclaimer = result.get("disclaimer")
        if not isinstance(disclaimer, str) or not disclaimer.strip():
            raise PartnerInferenceError("Partner response is missing its disclaimer.")
        return {
            "source": "model",
            "predictedLabel": prediction,
            "riskLevel": risk,
            "screeningFlag": bool(result.get("screening_flag")),
            "malignancyScore": score,
            "scoresAreCalibrated": False,
            "scores": class_scores,
            "scoreSource": "cnn_auxiliary",
            "scoreSemantics": result.get("auxiliary_class_score_semantics"),
            "diagnosisLevel": "binary",
            "subtypeAvailable": False,
            "subtypeUnavailableReason": "The final trained fusion model outputs BENIGN/MALIGNANT only; CNN class scores are auxiliary and do not constitute a validated subtype prediction.",
            "modelName": "Partner tri-modal melanoma hybrid",
            "modelVersion": "teammate_partner_v1",
            "inputImageId": image_ids[0],
            "numImages": len(images),
            "inputMetadata": {
                "ageProvided": age is not None,
                "sexProvided": sex != "unknown",
                "localizationProvided": bool(localization),
            },
            "streamScores": stream_scores,
            "thresholds": thresholds,
            "skinToneIta": result.get("skin_tone_ita"),
            "disclaimer": disclaimer,
            "researchMode": research_mode,
            "explanationAvailable": False,
        }
