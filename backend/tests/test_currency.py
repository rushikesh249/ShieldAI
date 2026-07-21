import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_validation_service():
    with patch("app.services.currency_ai.CurrencyAIService._validate_image_with_gemini") as mock:
        mock.return_value = {
            "is_single_indian_note": True,
            "detected_category": "Indian Currency Note",
            "detected_denomination": "₹500",
            "detected_side": "Front",
            "quality_status": "Sufficient",
            "validation_reason": "Single valid Indian ₹500 note detected."
        }
        yield mock

@pytest.fixture
def mock_forensic_service():
    with patch("app.services.currency_ai.CurrencyAIService._analyze_forensics_with_gemini") as mock:
        mock.return_value = {
            "verdict": "Suspicious",
            "summary_explanation": "Windowed security thread appears drawn on.",
            "features": [
                {
                    "id": "sec_thread",
                    "name": "Windowed Security Thread",
                    "status": "Inconsistency",
                    "observation": "Thread is drawn on and does not color shift.",
                    "confidence": 95,
                    "boundingBox": {"x": 0.5, "y": 0.5, "width": 0.1, "height": 0.1}
                }
            ],
            "evidence": ["Note feels fake."]
        }
        yield mock


def test_currency_analyze_mocked(client, mock_validation_service, mock_forensic_service, tmp_path):
    # Create a dummy image file
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"dummy image content")
    
    # We must patch the save_upload_file since dummy bytes won't pass PIL verification
    with patch("app.api.currency.save_upload_file", return_value=img_path):
        with patch("PIL.Image.open") as mock_img:
            # mock PIL verify
            mock_img.return_value.verify = MagicMock()
            mock_img.return_value.size = (100, 100)
            
            with open(img_path, "rb") as f:
                response = client.post(
                    "/api/v1/currency/analyze",
                    files={"file": ("test.jpg", f, "image/jpeg")},
                    data={"denomination": "₹500", "note_side": "Front"}
                )

    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["riskLevel"] == "High Risk"
    assert data["confidenceScore"] >= 50
    assert len(data["features"]) == 1
    assert data["features"][0]["status"] == "Inconsistency"
    # Ensure evidence includes Gemini evidence + Risk Engine recommendations
    assert any("Note feels fake" in e for e in data["evidence"])
