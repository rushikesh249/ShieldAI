"""
ShieldAI Backend — Currency Verification Schemas

Mirrors the frontend TypeScript types in ``src/lib/types/currency.ts``.
Includes OpenAPI documentation examples for Swagger UI.
"""

from __future__ import annotations

from typing import List, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field, model_validator


# ── Enums / Literals ─────────────────────────────────────────────────────────

CurrencyDenomination = Literal["₹100", "₹200", "₹500", "₹2000"]
CurrencyNoteSide = Literal["Front", "Reverse"]
CaptureType = Literal["Single Image", "Front + Reverse"]
FeatureStatus = Literal["Consistent", "Review", "Inconsistency", "Unknown"]
CurrencyRiskLevel = Literal["Low Risk", "Review Recommended", "High Risk"]


# ── Schemas ──────────────────────────────────────────────────────────────────

class BoundingBox(BaseModel):
    """Optional coordinates for highlighting suspicious regions in UI."""
    x: float = Field(..., description="X coordinate (normalized 0.0 to 1.0).", examples=[0.25])
    y: float = Field(..., description="Y coordinate (normalized 0.0 to 1.0).", examples=[0.25])
    width: float = Field(..., description="Width (normalized 0.0 to 1.0).", examples=[0.1])
    height: float = Field(..., description="Height (normalized 0.0 to 1.0).", examples=[0.1])


class SecurityFeature(BaseModel):
    """A single currency security feature inspection result."""

    id: str = Field(..., description="Internal ID of the feature (e.g. 'sec_thread').", examples=["sec_thread"])
    name: str = Field(..., description="Human-readable name.", examples=["Windowed Security Thread"])
    status: FeatureStatus = Field(..., description="Detected status of the feature.", examples=["Consistent"])
    observation: str = Field(..., description="Explanation of what was observed.", examples=["Thread is present and colour shifts from green to blue."])
    confidence: Optional[int] = Field(None, ge=0, le=100, description="Confidence in this specific feature observation.", examples=[95])
    bounding_box: Optional[BoundingBox] = Field(None, alias="boundingBox", description="Optional coordinates highlighting the feature.")

    model_config = {"populate_by_name": True}


class AuthenticityCheck(BaseModel):
    """A single note authenticity validation check (e.g. check for 'MANORANJAN BANK')."""
    check_name: str
    checkName: Optional[str] = None
    passed: bool
    detected: str
    expected: str

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def populate_compat(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cn = data.get("check_name") or data.get("checkName")
            if cn:
                data["check_name"] = cn
                data["checkName"] = cn
        return data


class CurrencyAnalysisResult(BaseModel):
    """Complete currency analysis result — matches frontend ``CurrencyAnalysisResult``."""

    id: str = Field(..., description="Unique internal identifier for the session.")
    status: str = Field(..., description="Verdict status of the note (Genuine, Counterfeit, Suspicious).", examples=["Counterfeit"])
    confidence: int = Field(..., ge=0, le=100, description="Confidence score.")
    risk_level: str = Field(..., description="Overall risk level (High, Medium, Low).", examples=["High"])
    detected_features: List[str] = Field(default_factory=list)
    missing_features: List[str] = Field(default_factory=list)
    authenticity_checks: List[AuthenticityCheck] = Field(default_factory=list)
    reason: str = Field(..., description="Verdict rationale.")
    recommendation: str = Field(..., description="Actionable recommendation.")
    limitations: str = Field(..., description="Analysis limitations.")
    extracted_text: Optional[str] = None

    # Compatibility and UI overlays (camelCase & legacy names as explicit model fields)
    riskLevel: Optional[str] = None
    confidenceScore: Optional[int] = None
    confidence_score: Optional[int] = None
    detectedFeatures: List[str] = Field(default_factory=list)
    missingFeatures: List[str] = Field(default_factory=list)
    authenticityChecks: List[AuthenticityCheck] = Field(default_factory=list)
    genuineIndicators: List[str] = Field(default_factory=list)
    genuine_indicators: List[str] = Field(default_factory=list)
    counterfeitIndicators: List[str] = Field(default_factory=list)
    counterfeit_indicators: List[str] = Field(default_factory=list)
    authenticitySummary: Optional[str] = None
    authenticity_summary: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    
    features: List[SecurityFeature] = Field(default_factory=list, description="List of analyzed security features.")
    denomination: Optional[str] = None
    serial_number: Optional[str] = None
    serialNumber: Optional[str] = None
    processing_time: Optional[str] = None
    processingTime: Optional[str] = None
    image_url: Optional[str] = None
    imageUrl: Optional[str] = None
    timestamp: str = Field(..., description="ISO-8601 timestamp of analysis completion.")

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def populate_compat_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # map confidence <-> confidence_score
            conf = data.get("confidence")
            conf_score = data.get("confidence_score") or data.get("confidenceScore")
            if conf is None and conf_score is not None:
                data["confidence"] = conf_score
            
            # Ensure both are set
            if data.get("confidence") is not None:
                data["confidence_score"] = data["confidence"]
                data["confidenceScore"] = data["confidence"]

            # map risk_level <-> riskLevel
            rl = data.get("risk_level") or data.get("riskLevel")
            if rl:
                legacy_map = {
                    "High": "High Risk",
                    "Medium": "Review Recommended",
                    "Low": "Low Risk",
                    "High Risk": "High Risk",
                    "Review Recommended": "Review Recommended",
                    "Low Risk": "Low Risk"
                }
                short_map = {
                    "High Risk": "High",
                    "Review Recommended": "Medium",
                    "Low Risk": "Low",
                    "High": "High",
                    "Medium": "Medium",
                    "Low": "Low"
                }
                data["risk_level"] = short_map.get(rl, rl)
                data["riskLevel"] = legacy_map.get(rl, rl)

            # map authenticity_summary <-> authenticitySummary
            asum = data.get("authenticity_summary") or data.get("authenticitySummary")
            if asum:
                data["authenticity_summary"] = asum
                data["authenticitySummary"] = asum

            # map detected_features / missing_features to camelCase aliases
            df = data.get("detected_features") or data.get("detectedFeatures")
            if df:
                data["detected_features"] = df
                data["detectedFeatures"] = df
            
            mf = data.get("missing_features") or data.get("missingFeatures")
            if mf:
                data["missing_features"] = mf
                data["missingFeatures"] = mf
                
            ac = data.get("authenticity_checks") or data.get("authenticityChecks")
            if ac:
                data["authenticity_checks"] = ac
                data["authenticityChecks"] = ac

            sn = data.get("serial_number") or data.get("serialNumber")
            if sn:
                data["serial_number"] = sn
                data["serialNumber"] = sn

            pt = data.get("processing_time") or data.get("processingTime")
            if pt:
                data["processing_time"] = pt
                data["processingTime"] = pt

            iu = data.get("image_url") or data.get("imageUrl")
            if iu:
                data["image_url"] = iu
                data["imageUrl"] = iu

            # fallback values for required fields
            if "status" not in data:
                data["status"] = "Suspicious"
            if "confidence" not in data:
                data["confidence"] = 0
                data["confidence_score"] = 0
                data["confidenceScore"] = 0
            if "risk_level" not in data:
                data["risk_level"] = "High"
                data["riskLevel"] = "High Risk"
            if "reason" not in data:
                data["reason"] = data.get("authenticity_summary") or "No validation detail provided."
            if "recommendation" not in data:
                data["recommendation"] = "Verify note authenticity manually."
            if "limitations" not in data:
                data["limitations"] = "RGB image analysis has inherent validation limitations."
        return data


