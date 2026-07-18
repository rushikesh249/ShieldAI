"""
ShieldAI Backend — Currency AI Service

Integrates Gemini Vision for explainable counterfeit currency detection.
Returns comprehensive authenticity assessment including genuine indicators,
counterfeit indicators, and bounding-box coordinates for UI overlays.
"""

from __future__ import annotations

import json
import time
import uuid
import datetime
from pathlib import Path
from typing import Any, Dict

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.currency import CurrencyDenomination, CurrencyAnalysisResult
from app.services.gemini import GeminiFraudService
from app.services.feature_fusion import FeatureFusionLayer
from app.services.recommendation import RecommendationEngine
from app.services.risk_engine import AIRiskEngine

try:
    import tensorflow as tf
    import numpy as np
    from PIL import Image
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = get_logger(__name__)

# ── Knowledge Base ────────────────────────────────────────────────────────────
KB_DIR = Path(__file__).resolve().parent.parent / "data"
FEATURES_JSON_PATH = KB_DIR / "currency_features.json"


def _load_features_db() -> Dict[str, Any]:
    if FEATURES_JSON_PATH.exists():
        with open(FEATURES_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


CURRENCY_FEATURES_DB = _load_features_db()

# ── Vision Prompt ─────────────────────────────────────────────────────────────
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "currency"
VISION_PROMPT_TEMPLATE = (
    PROMPTS_DIR / "vision_prompt.txt"
).read_text(encoding="utf-8") if (PROMPTS_DIR / "vision_prompt.txt").exists() else ""


# ── Gemini Vision Schema ──────────────────────────────────────────────────────
class CurrencyVisionResponse:
    """Schema shape expected from Gemini for currency analysis."""
    pass


class CurrencyAIService:
    """Service handling counterfeit currency detection using Gemini Vision AI."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.tf_model = None
        self.gemini = GeminiFraudService()

        # Optionally load TensorFlow model for a secondary signal
        self.model_path = Path(__file__).resolve().parent.parent.parent / "models" / "currency_model.h5"
        self._load_tf_model()

    def _load_tf_model(self) -> None:
        """Loads the TF model gracefully — runs in MOCK mode if unavailable."""
        if not TF_AVAILABLE:
            logger.warning("TensorFlow/PIL not installed. TF model running in MOCK mode.")
            return

        if not self.model_path.exists():
            logger.warning("Currency TF model not found at %s. Running in MOCK mode.", self.model_path)
            return

        try:
            self.tf_model = tf.keras.models.load_model(str(self.model_path))
            logger.info("Successfully loaded TensorFlow currency model.")
        except Exception as e:
            logger.error("Failed to load TensorFlow model: %s", str(e))

    def _predict_tf(self, image_path: Path) -> tuple[str, float]:
        """Runs image through TF model. Returns (prediction, confidence)."""
        if self.tf_model is None or not TF_AVAILABLE:
            # Mock: use filename hint for testing
            if "fake" in image_path.name.lower():
                return "Fake", 0.95
            return "Genuine", 0.88

        try:
            img = Image.open(image_path).convert("RGB").resize((224, 224))
            img_array = np.asarray(img, dtype=np.float32)
            img_array = (img_array / 127.5) - 1  # Normalize to [-1, 1]
            img_array = np.expand_dims(img_array, axis=0)

            predictions = self.tf_model.predict(img_array)
            idx = int(np.argmax(predictions[0]))
            confidence = float(predictions[0][idx])
            pred = "Fake" if idx == 1 else "Genuine"
            return pred, confidence
        except Exception as e:
            logger.error("TF Inference failed: %s", str(e))
            return "Genuine", 0.5  # Fallback — don't crash the pipeline

    def _analyze_gemini(self, image_path: Path, mime_type: str, denomination: str) -> Dict[str, Any]:
        """
        Calls Gemini Vision with the enhanced currency prompt.
        Returns parsed JSON with features, genuine_indicators, counterfeit_indicators,
        authenticity_summary, and evidence.
        """
        # Read prompt dynamically to allow live edits without restart
        prompt_template = (
            PROMPTS_DIR / "vision_prompt.txt"
        ).read_text(encoding="utf-8") if (PROMPTS_DIR / "vision_prompt.txt").exists() else VISION_PROMPT_TEMPLATE

        expected_features = CURRENCY_FEATURES_DB.get(denomination, [])
        prompt_text = prompt_template.replace(
            "{denomination}", denomination
        ).replace(
            "{expected_features_json}", json.dumps(expected_features, indent=2, ensure_ascii=False)
        )

        if not self.gemini.client:
            raise ValueError("Gemini client not initialized — check GEMINI_API_KEY.")

        # Upload image via Gemini Files API
        uploaded_file = self.gemini.client.files.upload(
            file=str(image_path),
            config={"mime_type": mime_type}
        )

        from google.genai import types as genai_types

        # Use free-form JSON response (no typed schema since our schema is complex/nested)
        config = genai_types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
        )

        response = self.gemini.client.models.generate_content(
            model=self.gemini.model_name,
            contents=[prompt_text, uploaded_file],
            config=config,
        )

        try:
            raw = response.text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini currency response as JSON: %s | raw: %s", str(e), response.text[:500])
            raise ValueError("Invalid JSON from Gemini currency analysis")

    def _validate_image(self, image_path: Path) -> None:
        """Validates the image is not corrupted and within size limits."""
        try:
            from PIL import Image as _Img
            img = _Img.open(image_path)
            img.verify()
            img = _Img.open(image_path)
            if img.size[0] > 8000 or img.size[1] > 8000:
                raise ValueError("Image dimensions too large (max 8000x8000).")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Corrupted or invalid image: {str(e)}")

    def analyze(self, image_path: Path, mime_type: str, denomination: str) -> Dict[str, Any]:
        """
        AI Decision Pipeline with strict validation:
        1. Validate Image (not corrupted).
        2. Call Gemini Vision with strict two-step primary/secondary prompt.
        3. Local OCR/Keyword Override: Check for parody/novelty text.
        4. Validate Confidence & Status rules (Genuine must have confidence > 85).
        5. Return standardized, fail-safe JSON.
        """
        start_total = time.perf_counter()
        
        # 1. Fallback Fail-Safe Template
        fail_safe_verdict = {
            "id": f"cur_{uuid.uuid4().hex[:8]}",
            "status": "Suspicious",
            "confidence": 0,
            "risk_level": "High",
            "detected_features": [],
            "missing_features": [],
            "authenticity_checks": [
                {
                    "check_name": "AI Model Call",
                    "passed": False,
                    "detected": "AI Connection Failure / Timeout",
                    "expected": "Active API response"
                }
            ],
            "reason": "Unable to verify note authenticity. Safety fallback triggered.",
            "recommendation": "Do not accept this note. Verify at the nearest bank or notify authorities.",
            "limitations": "This analysis is based solely on uploaded RGB images. It cannot conclusively authenticate UV, magnetic, or tactile security features.",
            "features": [],
            "authenticity_summary": "AI request failed or timed out. Falling back to Suspicious status.",
            "timestamp": datetime.datetime.now().isoformat()
        }

        try:
            # Validate image
            self._validate_image(image_path)
        except Exception as e:
            logger.error("Image validation failed: %s", str(e))
            fail_safe_verdict["reason"] = f"Invalid or corrupted image: {str(e)}"
            return fail_safe_verdict

        # 2. Primary & Secondary AI analysis
        gemini_res = None
        try:
            gemini_res = self._analyze_gemini(image_path, mime_type, denomination)
        except Exception as e:
            logger.error("Gemini Vision AI request failed: %s", str(e))
            fail_safe_verdict["reason"] = f"API request failed: {str(e)}"
            return fail_safe_verdict

        if not gemini_res or not isinstance(gemini_res, dict):
            logger.error("Invalid response from Gemini AI.")
            fail_safe_verdict["reason"] = "AI response parsing failed. Invalid JSON."
            return fail_safe_verdict

        # Extract parsed fields
        status = gemini_res.get("status", "Suspicious")
        confidence = gemini_res.get("confidence", 0)
        risk_level = gemini_res.get("risk_level", "High")
        detected_features = gemini_res.get("detected_features", [])
        missing_features = gemini_res.get("missing_features", [])
        authenticity_checks = gemini_res.get("authenticity_checks", [])
        reason = gemini_res.get("reason", "No verification detail provided.")
        recommendation = gemini_res.get("recommendation", "Verify note authenticity manually.")
        limitations = gemini_res.get("limitations", "RGB image analysis has inherent validation limitations.")
        features = gemini_res.get("features", [])
        extracted_text = gemini_res.get("extracted_text", "")
        
        # Determine the initial authenticity_summary
        authenticity_summary = gemini_res.get("authenticity_summary", reason)

        # 3. Local OCR and Parody Validation
        # Full text search for parody/novelty markings
        full_text_dump = json.dumps(gemini_res).lower()
        extracted_text_lower = extracted_text.lower()
        
        forbidden_keywords = [
            "manoranjan bank", "children bank", "movie money", "fake bank", 
            "specimen", "sample", "replica", "movie prop", "for motion picture use",
            "not legal tender", "training note", "copy", "souvenir", "toy bank",
            "points", "coupon", "play money"
        ]
        
        # Check direct or loose keywords
        detected_forbidden = [kw for kw in forbidden_keywords if kw in full_text_dump]
        
        # Let's also check for single-word versions or variations just to be absolutely sure
        parody_words = ["manoranjan", "monoranjan", "children bank", "toy bank", "coupon", "prop",
                        "motion picture", "specimen", "copy", "replica", "souvenir", "sample", 
                        "play money", "fake bank"]
        for word in parody_words:
            if word in full_text_dump and word not in detected_forbidden:
                detected_forbidden.append(word)

        # Validate mandatory keywords
        mandatory_keywords = [
            ("reserve bank of india", "RESERVE BANK OF INDIA"),
            ("भारतीय रिज़र्व बैंक", "भारतीय रिज़र्व बैंक"),
            ("rbi", "RBI"),
            ("promise to pay", "I PROMISE TO PAY"),
            ("governor", "GOVERNOR")
        ]
        
        # Denomination word mapping
        denom_clean = denomination.replace("₹", "").strip()
        denom_word_map = {
            "10": ("ten rupees", "TEN RUPEES"),
            "20": ("twenty rupees", "TWENTY RUPEES"),
            "50": ("fifty rupees", "FIFTY RUPEES"),
            "100": ("one hundred rupees", "ONE HUNDRED RUPEES"),
            "200": ("two hundred rupees", "TWO HUNDRED RUPEES"),
            "500": ("five hundred rupees", "FIVE HUNDRED RUPEES"),
            "2000": ("two thousand rupees", "TWO THOUSAND RUPEES")
        }
        if denom_clean in denom_word_map:
            mandatory_keywords.append(denom_word_map[denom_clean])
            
        missing_mandatory = []
        for kw_lower, kw_upper in mandatory_keywords:
            if kw_lower not in extracted_text_lower and kw_lower not in full_text_dump:
                missing_mandatory.append(kw_upper)

        if detected_forbidden or missing_mandatory:
            logger.warning("Local validation failed. Overriding status to Counterfeit. Forbidden: %s, Missing: %s", detected_forbidden, missing_mandatory)
            status = "Counterfeit"
            confidence = 99
            risk_level = "High"
            
            reasons = []
            if detected_forbidden:
                reasons.append(f"Detected forbidden text: {', '.join([f'\"{kw.upper()}\"' for kw in detected_forbidden])}")
            if missing_mandatory:
                reasons.append(f"Missing mandatory text: {', '.join([f'\"{kw}\"' for kw in missing_mandatory])}")
            reason = "Unofficial currency design detected. " + " ".join(reasons)
            
            recommendation = "Do not accept this note. Play notes, replica notes, and notes missing RBI markings are illegal."
            authenticity_summary = reason
            
            # Clear features since secondary validation must not run
            detected_features = []
            missing_features = []
            features = []
            
            # Re-initialize or append failed authenticity checks
            for kw in detected_forbidden:
                if not any(c.get("check_name") == "Forbidden Markings Check" and c.get("detected") == kw.upper() for c in authenticity_checks):
                    authenticity_checks.append({
                        "check_name": "Forbidden Markings Check",
                        "passed": False,
                        "detected": kw.upper(),
                        "expected": "Official RBI text only"
                    })
            for kw in missing_mandatory:
                if not any(c.get("check_name") == "Mandatory RBI Markings Check" and c.get("expected") == kw for c in authenticity_checks):
                    authenticity_checks.append({
                        "check_name": "Mandatory RBI Markings Check",
                        "passed": False,
                        "detected": "Missing/Not detected",
                        "expected": kw
                    })
        else:
            # If everything passed, make sure all mandatory checks are recorded as PASSED
            for kw_lower, kw_upper in mandatory_keywords:
                if not any(c.get("check_name") == "Mandatory RBI Markings Check" and c.get("expected") == kw_upper for c in authenticity_checks):
                    authenticity_checks.append({
                        "check_name": "Mandatory RBI Markings Check",
                        "passed": True,
                        "detected": kw_upper,
                        "expected": kw_upper
                    })
            if not any(c.get("check_name") == "Forbidden Markings Check" for c in authenticity_checks):
                authenticity_checks.append({
                    "check_name": "Forbidden Markings Check",
                    "passed": True,
                    "detected": "None",
                    "expected": "No parody or novelty text"
                })

        # 4. Strict Bug Fix: If Genuine, confidence must be > 85. If 0 or missing or low, demote to Suspicious.
        if status == "Genuine":
            if confidence is None or not isinstance(confidence, (int, float)) or confidence <= 0:
                logger.warning("Genuine note status had 0 or missing confidence score. Demoting to Suspicious.")
                status = "Suspicious"
                confidence = 0
                reason = "Unable to verify note authenticity. Confidence score could not be calculated."
                authenticity_summary = reason
            elif confidence < 85:
                logger.warning("Genuine status returned with low confidence %d%%. Demoting to Suspicious.", confidence)
                status = "Suspicious"
                confidence = 0
                reason = "Unable to verify note authenticity. Confidence too low."
                authenticity_summary = reason

        # If status is not set, fallback to Suspicious
        if status not in ("Genuine", "Counterfeit", "Suspicious"):
            status = "Suspicious"
            confidence = 0
            reason = "Unable to verify note authenticity."
            authenticity_summary = reason

        total_time_ms = (time.perf_counter() - start_total) * 1000
        logger.info("Decision Pipeline complete in %.2fms. Status: %s, Confidence: %d%%", total_time_ms, status, confidence)

        return {
            "id": f"cur_{uuid.uuid4().hex[:8]}",
            "status": status,
            "confidence": confidence,
            "risk_level": risk_level,
            "detected_features": detected_features,
            "missing_features": missing_features,
            "authenticity_checks": authenticity_checks,
            "reason": reason,
            "recommendation": recommendation,
            "limitations": limitations,
            "features": features,
            "extracted_text": extracted_text,
            "authenticitySummary": authenticity_summary,
            "timestamp": datetime.datetime.now().isoformat()
        }


currency_ai_service = CurrencyAIService()
