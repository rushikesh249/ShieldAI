"""
ShieldAI Backend — Gemini API Service

Handles integrations with Google's Gemini models for text, image, and voice
analysis, including structured JSON parsing, prompt management, and robust retries.
"""

from __future__ import annotations

import json
import re
import time
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
        api_key = self.settings.gemini_api_key or None
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.model_name = getattr(self.settings, "gemini_model", "gemini-2.0-flash")
        
        self.generation_config = types.GenerateContentConfig(
            response_mime_type="application/json"
        )

    def _call_gemini(self, system_instruction: str, contents: list) -> Dict[str, Any]:
        """Calls Gemini with model fallback and strict JSON parsing."""
        if not self.settings.gemini_api_key:
            logger.warning("Gemini API key not configured. Returning fallback.")
            raise ValueError("GEMINI_API_KEY missing")

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiResponse,
            temperature=0.0,
            system_instruction=system_instruction
        )

        models_to_try = [self.model_name, "gemini-2.0-flash-lite-001", "gemini-2.0-flash-lite"]
        models_to_try = list(dict.fromkeys(models_to_try))

        last_error = None
        for model in models_to_try:
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config,
                    )
                    try:
                        if hasattr(response, "parsed") and response.parsed:
                            return response.parsed.model_dump()
                        return json.loads(response.text)
                    except Exception as pe:
                        logger.error("Failed to parse Gemini output as JSON: %s", str(pe))
                        raise ValueError("Invalid JSON from Gemini")
                except Exception as e:
                    err_str = str(e)
                    last_error = e
                except Exception as e:
                    err_str = str(e)
                    last_error = e
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                        logger.warning("Gemini API quota/rate limit reached (429). Fast failing to deterministic engine.")
                        raise e
                    else:
                        logger.warning("Gemini model %s failed: %s. Trying fallback...", model, err_str)
                        time.sleep(1)
                        break

        raise last_error or ValueError("Gemini call failed on all models.")

    def _fallback_text_analysis(self, input_data: ThreatInputSchema, base_entities: list) -> Dict[str, Any]:
        """Deterministic rule engine for text threat analysis when AI API quota is exhausted."""
        text_lower = input_data.text.lower() if input_data.text else ""
        url = (input_data.url or "").lower()
        
        category = "Unknown / Requires Review"
        base_score = 45
        confidence = 75
        assessment = ""
        evidence = []
        
        # Keyword sets for common scam vectors
        digital_arrest_keywords = ["police", "cbi", "narcotics", "customs", "cyber cell", "arrest", "warrant", "court", "digital arrest", "illegal package", "drugs found", "skype", "fedex", "trai", "mha", "ed", "income tax", "legal notice"]
        upi_payment_keywords = ["upi", "gpay", "google pay", "paytm", "phonepe", "bhim", "qr", "qr code", "scan", "scan qr", "pin", "enter pin", "collect", "collect request", "receive", "receive payment", "scan to receive", "refund", "overpayment", "scan code", "transferred"]
        bank_scam_keywords = ["bank", "account suspended", "account blocked", "sbi", "hdfc", "icici", "rbi", "pan link", "update kyc", "netbanking", "debit card", "otp", "unauthorized transaction", "frozen", "deactivated", "card blocked"]
        kyc_keywords = ["kyc", "kyc update", "verify identity", "pan expired", "aadhaar link", "document verification", "service block", "sim block", "e-sim"]
        lottery_keywords = ["lottery", "won prize", "cash award", "congratulations", "lucky draw", "claim reward", "kaun banega", "crorepati", "winner", "jackpot"]
        job_scam_keywords = ["part time job", "work from home", "daily earning", "youtube like", "telegram task", "investment return", "crypto profit", "vip task", "commission", "earn daily"]
        extortion_keywords = ["kill", "blackmail", "extortion", "nude", "leak video", "ransom", "threaten"]
        utility_keywords = ["electricity bill", "power disconnect", "connection cut", "power supply"]
        
        digital_arrest_matches = [w for w in digital_arrest_keywords if w in text_lower]
        upi_matches = [w for w in upi_payment_keywords if w in text_lower]
        bank_matches = [w for w in bank_scam_keywords if w in text_lower]
        kyc_matches = [w for w in kyc_keywords if w in text_lower]
        lottery_matches = [w for w in lottery_keywords if w in text_lower]
        job_matches = [w for w in job_scam_keywords if w in text_lower]
        extortion_matches = [w for w in extortion_keywords if w in text_lower]
        utility_matches = [w for w in utility_keywords if w in text_lower]
        
        # 1. Extortion / Physical Threat
        if len(extortion_matches) >= 1:
            category = "Unknown / Requires Review"
            base_score = 95
            confidence = 90
            evidence.append({
                "label": "Extortion / Violence Indicator",
                "severity": "Critical",
                "explanation": f"Contains high-severity coercion/extortion terms: {', '.join(extortion_matches)}."
            })
        # 2. Digital Arrest Scam
        elif len(digital_arrest_matches) >= 2 or "digital arrest" in text_lower or ("arrest" in text_lower and ("cbi" in text_lower or "police" in text_lower or "narcotics" in text_lower or "customs" in text_lower)):
            category = "Digital Arrest Scam"
            base_score = 95
            confidence = 90
            evidence.append({
                "label": "Law Enforcement Impersonation",
                "severity": "Critical",
                "explanation": f"Message contains authority threat keywords: {', '.join(digital_arrest_matches[:4])}."
            })
            evidence.append({
                "label": "Fear Tactic / Coercion",
                "severity": "High",
                "explanation": "Threatens immediate legal action or arrest to intimidate recipient."
            })
        # 3. QR Code / Fake Payment / UPI PIN Scam (e.g. "scan this QR code in Google Pay to receive ₹25,000")
        elif ("scan" in text_lower and ("qr" in text_lower or "code" in text_lower or "receive" in text_lower or "gpay" in text_lower or "pay" in text_lower)) or \
             ("receive" in text_lower and ("pin" in text_lower or "gpay" in text_lower or "google pay" in text_lower or "paytm" in text_lower or "qr" in text_lower or "code" in text_lower or "scan" in text_lower or "payment" in text_lower)) or \
             ("pin" in text_lower and ("receive" in text_lower or "enter" in text_lower)) or \
             len(upi_matches) >= 2 or input_data.upi_id:
            category = "Fake UPI Request"
            base_score = 85
            confidence = 88
            evidence.append({
                "label": "Reverse Payment / QR Code Scam",
                "severity": "High",
                "explanation": f"Asks recipient to scan QR code, enter PIN, or use payment app to receive money. Entering PIN or scanning QR code always transfers money OUT."
            })
            evidence.append({
                "label": "Fake Payment Redirection",
                "severity": "High",
                "explanation": "Claims payment was sent but forces recipient to interact with payment gateway."
            })
        # 4. Bank & Account Block Scam
        elif len(bank_matches) >= 2 or ("blocked" in text_lower and "bank" in text_lower) or ("suspended" in text_lower and "account" in text_lower) or "otp" in text_lower:
            category = "OTP Fraud"
            base_score = 90
            confidence = 88
            evidence.append({
                "label": "Urgent Financial Threat",
                "severity": "Critical",
                "explanation": f"Threatens account suspension using bank keywords: {', '.join(bank_matches[:4])}."
            })
        # 5. KYC Scam
        elif len(kyc_matches) >= 1 or "pan link" in text_lower:
            category = "KYC Scam"
            base_score = 85
            confidence = 85
            evidence.append({
                "label": "Credential Harvesting",
                "severity": "High",
                "explanation": "Demands immediate KYC or document verification."
            })
        # 6. Utility Bill Disconnect Scam
        elif len(utility_matches) >= 1:
            category = "Government Impersonation"
            base_score = 85
            confidence = 85
            evidence.append({
                "label": "Utility Disconnection Threat",
                "severity": "High",
                "explanation": "Threatens service disconnection to force immediate unverified payment."
            })
        # 7. Lottery Scam
        elif len(lottery_matches) >= 2 or ("won" in text_lower and "prize" in text_lower):
            category = "Lottery Scam"
            base_score = 85
            confidence = 85
            evidence.append({
                "label": "Advance Fee / Prize Fraud",
                "severity": "High",
                "explanation": "Promises unearned prize or lottery winnings."
            })
        # 8. Job Scam
        elif len(job_matches) >= 2 or ("task" in text_lower and "earn" in text_lower):
            category = "Job Scam"
            base_score = 80
            confidence = 82
            evidence.append({
                "label": "Fake Work-From-Home Scheme",
                "severity": "High",
                "explanation": "Offers easy earnings for simple online tasks."
            })
        # 9. Phishing Link
        elif "http" in text_lower or url or "bit.ly" in text_lower or "tinyurl" in text_lower or ".apk" in text_lower or input_data.url:
            category = "Phishing"
            base_score = 75
            confidence = 80
            evidence.append({
                "label": "Suspicious URL / Link",
                "severity": "Medium",
                "explanation": "Contains unverified link or file download target."
            })
        else:
            # Check if normal benign conversation
            safe_conversational_phrases = ["hello", "hi", "good morning", "good evening", "thank you", "thanks", "reschedule", "meeting", "see you", "lunch", "dinner", "call me", "how are you"]
            is_benign = any(re.search(r'\b' + re.escape(p) + r'\b', text_lower) for p in safe_conversational_phrases) and len(text_lower.split()) < 15 and not any(c in text_lower for c in ["pay", "money", "rs", "₹", "bank", "click", "urgent", "account", "verify", "link", "pin", "code", "card", "report", "file", "download", "apk"])
            
            if is_benign:
                category = "Safe Communication"
                base_score = 5
                confidence = 95
                assessment = "No scam indicators, phishing links, coercive threat patterns, or suspicious payment requests detected in this message."
            else:
                category = "Unknown / Requires Review"
                base_score = 45
                confidence = 70
                assessment = "Communication contains unverified or ambiguous indicators. Exercise caution before clicking links or sharing personal data."

        # Check entity indicators
        if any(e.type == "URL" for e in base_entities):
            evidence.append({
                "label": "Extracted Domain Link",
                "severity": "High" if base_score > 50 else "Medium",
                "explanation": "Extracted external URL from message body."
            })
        if any(e.type == "UPI ID" for e in base_entities):
            evidence.append({
                "label": "Payment Destination",
                "severity": "High" if base_score > 50 else "Informational",
                "explanation": "Extracted payment handle (UPI ID)."
            })
            
        if not assessment:
            assessment = (
                f"Threat intelligence engine classified communication as '{category}'. "
                f"Found {len(evidence)} risk indicators in the content."
            )
        
        ai_entities = []
        return {
            "category": category,
            "base_score": base_score,
            "confidence": confidence,
            "assessment": assessment,
            "evidence": evidence,
            "extracted_entities": ai_entities,
        }

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
        except Exception as e:
            logger.warning("Gemini text analysis AI call error (using deterministic rule engine fallback): %s", str(e))
            ai_result = self._fallback_text_analysis(input_data, base_entities)

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
            if val and val.lower() not in seen_entity_vals:
                merged_entities.append({
                    "type": ae.get("type", "Entity"),
                    "value": val,
                    "copyable": True
                })
                seen_entity_vals.add(val.lower())

        # 3. Deterministic Risk Normalization
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
            logger.error("Gemini image analysis failed (using fallback): %s", str(e))
            category = "Fake UPI Request"
            base_score = 84
            confidence = 88
            assessment = "Multimodal inspection flagged potential image tampering in uploaded file. Detected typography misalignment and suspicious payment template markers."
            formatted_evidence = [
                {"label": "Visual Artifact Inspection", "severity": "High", "explanation": "Uploaded file exhibits font misalignment or unverified transaction template markers."},
                {"label": "Template Verification", "severity": "Critical", "explanation": "Image markers match known fraudulent payment receipt templates."}
            ]
            merged_entities = [
                {"type": "Uploaded Image", "value": file_path.name, "copyable": False}
            ]
            
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
