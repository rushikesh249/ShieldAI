"""
ShieldAI Backend — Gemini API Service

Handles integrations with Google's Gemini models for text, image, and voice
analysis, including structured JSON parsing, prompt management, and robust retries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.fraud import ThreatInputSchema
from app.services.entity_extraction import EntityExtractor
from app.services.recommendation import RecommendationEngine
from app.services.risk_engine import AIRiskEngine

logger = get_logger(__name__)

# Load prompts
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "fraud"

def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

SYSTEM_PROMPT = _load_prompt("system_prompt_v1.txt")
COMPLAINT_PROMPT = _load_prompt("complaint_prompt_v1.txt")


class GeminiEvidence(BaseModel):
    label: str
    severity: str
    explanation: str

class GeminiEntity(BaseModel):
    type: str
    value: str

class GeminiResponse(BaseModel):
    category: str
    base_score: int
    confidence: int
    assessment: str
    evidence: list[GeminiEvidence]
    extracted_entities: list[GeminiEntity]

class GeminiFraudService:
    """Wrapper for Gemini interactions ensuring structured responses."""

    def __init__(self) -> None:
        self.settings = get_settings()
        # The new SDK automatically picks up GEMINI_API_KEY from environment,
        # but we can explicitly pass it if needed.
        api_key = self.settings.gemini_api_key or None
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.model_name = getattr(self.settings, "gemini_model", "gemini-3.5-flash")
        
        # Force JSON response type
        self.generation_config = types.GenerateContentConfig(
            response_mime_type="application/json"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_gemini(self, system_instruction: str, contents: list) -> Dict[str, Any]:
        """Calls Gemini and parses the strict JSON output."""
        if not self.settings.gemini_api_key:
            logger.warning("Gemini API key not configured. Returning fallback.")
            raise ValueError("GEMINI_API_KEY missing")

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiResponse,
            temperature=0.0,
            system_instruction=system_instruction
        )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            logger.error("Failed to parse Gemini output as JSON: %s", response.text)
            raise ValueError("Invalid JSON from Gemini")

    def analyze_text(self, input_data: ThreatInputSchema) -> Dict[str, Any]:
        """Analyse text using Gemini and combine with deterministic engines."""
        prompt = (
            f"Source: {input_data.source}\n"
            f"Sender/Phone: {input_data.phone_number or 'N/A'}\n"
            f"UPI ID: {input_data.upi_id or 'N/A'}\n"
            f"URL: {input_data.url or 'N/A'}\n\n"
            f"Communication Content:\n{input_data.text}"
        )
        
        # 1. Deterministic Entity Extraction
        base_entities = EntityExtractor.extract_all(input_data.text)
        if input_data.phone_number:
            base_entities.extend(EntityExtractor.extract_phones(input_data.phone_number))
        if input_data.upi_id:
            base_entities.extend(EntityExtractor.extract_upis(input_data.upi_id))
        if input_data.url:
            base_entities.extend(EntityExtractor.extract_urls(input_data.url))
            
        try:
            # 2. AI Analysis
            ai_result = self._call_gemini(SYSTEM_PROMPT, [prompt])
            category = ai_result.get("category", "Unknown / Requires Review")
            base_score = ai_result.get("base_score", 0)
            confidence = ai_result.get("confidence", 50)
            assessment = ai_result.get("assessment", "Analysis complete.")
            evidence = ai_result.get("evidence", [])
            ai_entities = ai_result.get("extracted_entities", [])
            
            # Map AI evidence to schemas
            formatted_evidence = []
            for ev in evidence:
                formatted_evidence.append({
                    "label": ev.get("label", "Indicator"),
                    "severity": ev.get("severity", "Informational"),
                    "explanation": ev.get("explanation", "")
                })
                
            # Merge entities
            merged_entities = [e.model_dump() for e in base_entities]
            seen_entity_vals = {e.value.lower() for e in base_entities}
            for ae in ai_entities:
                val = ae.get("value", "")
                if val.lower() not in seen_entity_vals:
                    merged_entities.append({
                        "type": ae.get("type", "Entity"),
                        "value": val,
                        "copyable": True
                    })
                    seen_entity_vals.add(val.lower())
            
        except Exception as e:
            logger.error("Gemini text analysis failed: %s", str(e))
            # Fallback
            category = "Unknown / Requires Review"
            base_score = 0
            confidence = 0
            assessment = "AI analysis failed or is unconfigured. Please review manually."
            formatted_evidence = []
            merged_entities = [e.model_dump() for e in base_entities]
            
        # 3. Deterministic Risk Normalization
        # EvidenceIndicator requires object to parse properly in risk engine if using strict typing, 
        # but dicts work if we construct objects or map it in risk engine.
        # Let's map it safely for risk engine.
        class _MockEv:
            def __init__(self, s):
                self.severity = s
        mock_evidence = [_MockEv(e["severity"]) for e in formatted_evidence]
        final_score, final_level = AIRiskEngine.calculate_risk(category, mock_evidence, base_score) # type: ignore
        
        # 4. Deterministic Recommendations
        recommendations = RecommendationEngine.get_recommendations(category, final_level)
        
        return {
            "level": final_level,
            "score": final_score,
            "confidence": confidence,
            "category": category,
            "assessment": assessment,
            "evidence": formatted_evidence,
            "entities": merged_entities,
            "recommendations": recommendations,
        }

    def analyze_image(self, file_path: Path, mime_type: str) -> Dict[str, Any]:
        """Analyse an image using Gemini Vision."""
        try:
            # Upload to Gemini File API (required for multimodal)
            uploaded_file = self.client.files.upload(file=str(file_path), config={'mime_type': mime_type})
            
            prompt = "Analyse this image (screenshot or document) for signs of digital fraud, scams, or malicious intent."
            ai_result = self._call_gemini(SYSTEM_PROMPT, [uploaded_file, prompt])
            
            category = ai_result.get("category", "Unknown / Requires Review")
            base_score = ai_result.get("base_score", 0)
            confidence = ai_result.get("confidence", 50)
            assessment = ai_result.get("assessment", "Analysis complete.")
            evidence = ai_result.get("evidence", [])
            ai_entities = ai_result.get("extracted_entities", [])
            
            formatted_evidence = [
                {"label": ev.get("label", ""), "severity": ev.get("severity", "Informational"), "explanation": ev.get("explanation", "")}
                for ev in evidence
            ]
            
            merged_entities = [
                {"type": ae.get("type", "Entity"), "value": ae.get("value", ""), "copyable": True}
                for ae in ai_entities
            ]
            
        except Exception as e:
            logger.error("Gemini image analysis failed: %s", str(e))
            category = "Unknown / Requires Review"
            base_score = 0
            confidence = 0
            assessment = "AI image analysis failed. Please review manually."
            formatted_evidence = []
            merged_entities = []
            
        class _MockEv:
            def __init__(self, s):
                self.severity = s
        mock_evidence = [_MockEv(e["severity"]) for e in formatted_evidence]
        final_score, final_level = AIRiskEngine.calculate_risk(category, mock_evidence, base_score) # type: ignore
        recommendations = RecommendationEngine.get_recommendations(category, final_level)
        
        return {
            "level": final_level,
            "score": final_score,
            "confidence": confidence,
            "category": category,
            "assessment": assessment,
            "evidence": formatted_evidence,
            "entities": merged_entities,
            "recommendations": recommendations,
        }

    def analyze_voice(self, transcript: str, original_filename: str) -> Dict[str, Any]:
        """Analyse a voice transcript using Gemini."""
        input_data = ThreatInputSchema(
            source="Voice",
            text=f"[Transcript from {original_filename}]: {transcript}"
        )
        return self.analyze_text(input_data)

    def generate_complaint(self, input_data: Dict[str, Any], verdict: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an official complaint draft based on the threat."""
        prompt = (
            f"Source: {input_data.get('source', 'Unknown')}\n"
            f"Original Text: {input_data.get('text', 'N/A')}\n"
            f"Threat Category: {verdict.get('category', 'Unknown')}\n"
            f"Threat Assessment: {verdict.get('assessment', 'N/A')}\n"
            f"Entities Identified: {json.dumps(verdict.get('entities', []))}\n"
        )
        try:
            return self._call_gemini(COMPLAINT_PROMPT, [prompt])
        except Exception as e:
            logger.error("Complaint generation failed: %s", str(e))
            return {
                "summary": "Failed to generate complaint automatically.",
                "incident_description": "AI generation failed. Please describe the incident manually.",
                "evidence": [],
                "suggested_complaint": "AI generation failed.",
                "pdf_ready_json": {"title": "Incident Report", "date": "", "category": "", "body": "Failed to generate."}
            }

# Singleton
gemini_service = GeminiFraudService()
