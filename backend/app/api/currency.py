"""
ShieldAI Backend — Currency Verification Endpoints

Integrates TensorFlow and Gemini Vision for currency security feature 
inspection and counterfeit detection.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.core.logging import get_logger
from app.schemas.currency import CurrencyDenomination, CurrencyNoteSide
from app.services.currency_ai import currency_ai_service
from app.utils.upload import save_upload_file
from app.services.network_cache import session_store
from app.schemas.currency import CurrencyAnalysisResult
from app.utils.response import success_response, error_response

logger = get_logger(__name__)

router = APIRouter(prefix="/currency", tags=["Currency Verification"])

# Common OpenAPI response for 500 errors
SERVER_ERROR_RESPONSE = {
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "message": "Failed to analyze currency.",
                    "data": None,
                    "errors": [{"field": "ai", "message": "API timeout", "type": "timeout"}],
                    "timestamp": "2024-01-01T12:00:00Z",
                    "request_id": "abc-123"
                }
            }
        }
    }
}

BAD_REQUEST_RESPONSE = {
    400: {
        "description": "Bad Request - Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "message": "Invalid file type.",
                    "data": None,
                    "errors": [{"field": "file", "message": "Only images are allowed.", "type": "validation"}],
                    "timestamp": "2024-01-01T12:00:00Z",
                    "request_id": "abc-123"
                }
            }
        }
    }
}


@router.post(
    "/analyze",
    summary="Analyse Currency Image",
    description="Analyzes an uploaded currency note image for counterfeit indicators. Merges TensorFlow classification with Gemini Vision security feature verification, checking for watermarks, threads, and micro-printing.",
    responses={
        200: {
            "description": "Successful Currency Analysis",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Currency analysis complete.",
                        "data": {
                            "riskLevel": "High Risk",
                            "confidenceScore": 92,
                            "features": [
                                {
                                    "id": "sec_thread",
                                    "name": "Windowed Security Thread",
                                    "status": "Inconsistency",
                                    "observation": "Thread is drawn on and does not color shift.",
                                    "confidence": 95,
                                    "boundingBox": {"x": 0.4, "y": 0.1, "width": 0.05, "height": 0.8}
                                }
                            ],
                            "evidence": ["Security thread looks printed.", "Reject Currency", "Report Suspicious Note"]
                        },
                        "errors": None,
                        "timestamp": "2024-01-01T12:00:00Z",
                        "request_id": "abc-123"
                    }
                }
            }
        },
        **BAD_REQUEST_RESPONSE,
        **SERVER_ERROR_RESPONSE
    }
)
async def analyze_currency(
    request: Request,
    file: UploadFile = File(..., description="Currency note image (PNG, JPG, WEBP)"),
    denomination: str = Form("₹500", description="Note denomination (e.g. ₹500)"),
    note_side: str = Form("Front", description="Front or Reverse side of the note"),
):
    """Analyse an uploaded currency image for counterfeit indicators."""
    start_time = time.perf_counter()
    
    try:
        # Validate and save
        file_path = await save_upload_file(file, allowed_categories=["image"])
        
        # Analyze
        mime_type = file.content_type or "image/jpeg"
        verdict = currency_ai_service.analyze(file_path, mime_type, denomination)
        
        # Save session to shared store
        session_obj = CurrencyAnalysisResult(**verdict)
        session_store.save_dataset(session_obj)
        
        # Save scan to database for history
        from app.db.database import save_scan
        save_scan(session_obj.model_dump(mode="json"))
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "API Route Complete | route=/currency/analyze | duration=%.1fms", duration_ms
        )
        
        return success_response(
            data=session_obj.model_dump(mode="json"),
            message="Currency analysis complete.",
            request=request,
        )
    except ValueError as e:
        return error_response(message=str(e), status_code=400, request=request)
    except Exception as e:
        logger.exception("Currency analysis failed")
        return error_response(message="Failed to analyze currency.", status_code=500, request=request)


@router.post(
    "/counterfeit-detection",
    summary="Counterfeit Indian Currency Detection",
    description="Full production-ready endpoint that preprocesses the note (blur check, perspective crop, contrast enhance) and runs AI-assisted verification.",
)
async def counterfeit_detection(
    request: Request,
    file: UploadFile = File(..., description="Currency note image (PNG, JPG, JPEG, WEBP)"),
    denomination: str = Form("₹500", description="Note denomination (e.g. ₹500)"),
    note_side: str = Form("Front", description="Front or Reverse side"),
):
    """Secure endpoint for counterfeit note identification with image preprocessing."""
    start_time = time.perf_counter()
    try:
        # 1. Save uploaded file securely
        file_path = await save_upload_file(file, allowed_categories=["image"])
        
        # 2. Run image preprocessing (blur check, metadata strip, crop, perspective, CLAHE)
        from app.services.image_processing import ImagePreprocessor
        try:
            processed_path = ImagePreprocessor.preprocess(file_path)
        except ValueError as blur_err:
            return error_response(
                message=str(blur_err),
                status_code=400,
                request=request,
                errors=[{"field": "file", "message": str(blur_err), "type": "blur"}]
            )
            
        # 3. Analyze preprocessed image using AI Service
        mime_type = file.content_type or "image/jpeg"
        verdict = currency_ai_service.analyze(processed_path, mime_type, denomination)
        
        # 4. Save session to shared store
        session_obj = CurrencyAnalysisResult(**verdict)
        session_store.save_dataset(session_obj)
        
        # 5. Extract Serial Number from features
        serial_number = "Not detected"
        for feature in verdict.get("features", []):
            if feature.get("id") == "serial_number":
                obs = feature.get("observation", "")
                import re
                match = re.search(r'\b([0-9][A-Z]{2}\s*\d{6}|[A-Z0-9]{8,10})\b', obs, re.IGNORECASE)
                if match:
                    serial_number = match.group(1).replace(" ", "").upper()
                else:
                    words = re.findall(r'\b[A-Z0-9]{7,10}\b', obs, re.IGNORECASE)
                    if words:
                        serial_number = words[0].upper()
                break
        
        processing_time_sec = time.perf_counter() - start_time
        
        # Update extra metadata fields in the session object
        session_obj.denomination = denomination
        session_obj.serial_number = serial_number
        session_obj.serialNumber = serial_number
        session_obj.processing_time = f"{processing_time_sec:.1f} sec"
        session_obj.processingTime = f"{processing_time_sec:.1f} sec"
        session_obj.image_url = str(processed_path.name)
        session_obj.imageUrl = str(processed_path.name)
        
        # Save scan to database for history
        from app.db.database import save_scan
        save_scan(session_obj.model_dump(mode="json"))
        
        return success_response(
            data=session_obj.model_dump(mode="json"),
            message="Currency counterfeit detection complete.",
            request=request,
        )
    except ValueError as val_err:
        return error_response(message=str(val_err), status_code=400, request=request)
    except Exception as e:
        logger.exception("Counterfeit detection failed")
        return error_response(message="Failed to analyze currency counterfeit status.", status_code=500, request=request)


