import pytest
from unittest.mock import patch, MagicMock
from app.services.currency_ai import currency_ai_service

@pytest.fixture
def mock_tf_service():
    with patch("app.services.currency_ai.CurrencyAIService._predict_tf") as mock:
        mock.return_value = ("Genuine", 0.95)
        yield mock


def test_currency_analyze_genuine(client, mock_tf_service, tmp_path):
    img_path = tmp_path / "test_genuine.jpg"
    img_path.write_bytes(b"dummy image content")
    
    genuine_response = {
        "status": "Genuine",
        "confidence": 95,
        "risk_level": "Low",
        "detected_features": ["Mahatma Gandhi Portrait", "Windowed Security Thread"],
        "missing_features": [],
        "authenticity_checks": [
            {
                "check_name": "Official Bank Issuance",
                "passed": True,
                "detected": "RESERVE BANK OF INDIA",
                "expected": "RESERVE BANK OF INDIA"
            }
        ],
        "reason": "Note matches all expected RBI security features and text markings.",
        "recommendation": "Accept the note.",
        "limitations": "Standard visual scan limitations apply.",
        "extracted_text": "RESERVE BANK OF INDIA RBI भारतीय रिज़र्व बैंक FIVE HUNDRED RUPEES I Promise to Pay Governor",
        "features": [
            {
                "id": "sec_thread",
                "name": "Windowed Security Thread",
                "status": "Consistent",
                "observation": "Thread is present and shifts colour correctly."
            }
        ]
    }
    
    with patch("app.services.currency_ai.CurrencyAIService._analyze_gemini", return_value=genuine_response):
        with patch("app.api.currency.save_upload_file", return_value=img_path):
            with patch("PIL.Image.open") as mock_img:
                mock_img.return_value.verify = MagicMock()
                mock_img.return_value.size = (100, 100)
                
                with open(img_path, "rb") as f:
                    response = client.post(
                        "/api/v1/currency/analyze",
                        files={"file": ("test_genuine.jpg", f, "image/jpeg")},
                        data={"denomination": "₹500", "note_side": "Front"}
                    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "Genuine"
    assert data["riskLevel"] == "Low Risk"
    assert data["confidence"] == 95
    assert data["confidenceScore"] == 95
    assert "sec_thread" in [f["id"] for f in data["features"]]


def test_currency_analyze_parody_override(client, mock_tf_service, tmp_path):
    img_path = tmp_path / "test_fake.jpg"
    img_path.write_bytes(b"dummy image content")
    
    # AI returns Genuine, but extracted_text contains "MANORANJAN BANK"
    parody_response = {
        "status": "Genuine",
        "confidence": 90,
        "risk_level": "Low",
        "detected_features": ["Mahatma Gandhi Portrait"],
        "missing_features": [],
        "authenticity_checks": [],
        "reason": "Seems genuine.",
        "recommendation": "Accept.",
        "limitations": "None.",
        "extracted_text": "MANORANJAN BANK OF INDIA भारतीय रिज़र्व बैंक FIVE HUNDRED POINTS I Promise to Pay Governor",
        "features": []
    }
    
    with patch("app.services.currency_ai.CurrencyAIService._analyze_gemini", return_value=parody_response):
        with patch("app.api.currency.save_upload_file", return_value=img_path):
            with patch("PIL.Image.open") as mock_img:
                mock_img.return_value.verify = MagicMock()
                mock_img.return_value.size = (100, 100)
                
                with open(img_path, "rb") as f:
                    response = client.post(
                        "/api/v1/currency/analyze",
                        files={"file": ("test_fake.jpg", f, "image/jpeg")},
                        data={"denomination": "₹500", "note_side": "Front"}
                    )

    assert response.status_code == 200
    data = response.json()["data"]
    # Should be overridden to Counterfeit with 99 confidence
    assert data["status"] == "Counterfeit"
    assert data["confidence"] == 99
    assert data["riskLevel"] == "High Risk"
    assert "MANORANJAN" in data["reason"]
    # Check failed authenticity check exists
    failed_checks = [c for c in data["authenticityChecks"] if not c["passed"]]
    assert len(failed_checks) > 0
    assert any("Forbidden Markings Check" in c["checkName"] for c in failed_checks)


def test_currency_analyze_low_confidence_demotion(client, mock_tf_service, tmp_path):
    img_path = tmp_path / "test_low_conf.jpg"
    img_path.write_bytes(b"dummy image content")
    
    # Genuine but confidence is below 85 (e.g. 70)
    low_conf_response = {
        "status": "Genuine",
        "confidence": 70,
        "risk_level": "Low",
        "detected_features": [],
        "missing_features": [],
        "authenticity_checks": [],
        "reason": "Matches structure but image too blurry.",
        "recommendation": "Scan again.",
        "limitations": "Standard.",
        "extracted_text": "RESERVE BANK OF INDIA RBI भारतीय रिज़र्व बैंक FIVE HUNDRED RUPEES I Promise to Pay Governor",
        "features": []
    }
    
    with patch("app.services.currency_ai.CurrencyAIService._analyze_gemini", return_value=low_conf_response):
        with patch("app.api.currency.save_upload_file", return_value=img_path):
            with patch("PIL.Image.open") as mock_img:
                mock_img.return_value.verify = MagicMock()
                mock_img.return_value.size = (100, 100)
                
                with open(img_path, "rb") as f:
                    response = client.post(
                        "/api/v1/currency/analyze",
                        files={"file": ("test_low_conf.jpg", f, "image/jpeg")},
                        data={"denomination": "₹500", "note_side": "Front"}
                    )

    assert response.status_code == 200
    data = response.json()["data"]
    # Should be demoted to Suspicious with 0 confidence
    assert data["status"] == "Suspicious"
    assert data["confidence"] == 0
    assert "Confidence too low" in data["reason"]


def test_currency_analyze_missing_mandatory_text(client, mock_tf_service, tmp_path):
    img_path = tmp_path / "test_missing_text.jpg"
    img_path.write_bytes(b"dummy image content")
    
    # Missing reserve bank of india
    missing_response = {
        "status": "Genuine",
        "confidence": 95,
        "risk_level": "Low",
        "detected_features": [],
        "missing_features": [],
        "authenticity_checks": [],
        "reason": "Looks good.",
        "recommendation": "Accept.",
        "limitations": "Standard.",
        "extracted_text": "FIVE HUNDRED RUPEES I Promise to Pay Governor",
        "features": []
    }
    
    with patch("app.services.currency_ai.CurrencyAIService._analyze_gemini", return_value=missing_response):
        with patch("app.api.currency.save_upload_file", return_value=img_path):
            with patch("PIL.Image.open") as mock_img:
                mock_img.return_value.verify = MagicMock()
                mock_img.return_value.size = (100, 100)
                
                with open(img_path, "rb") as f:
                    response = client.post(
                        "/api/v1/currency/analyze",
                        files={"file": ("test_missing_text.jpg", f, "image/jpeg")},
                        data={"denomination": "₹500", "note_side": "Front"}
                    )

    assert response.status_code == 200
    data = response.json()["data"]
    # Should be overridden to Counterfeit with 99 confidence
    assert data["status"] == "Counterfeit"
    assert data["confidence"] == 99
    assert "Missing mandatory text" in data["reason"]
    failed_checks = [c for c in data["authenticityChecks"] if not c["passed"]]
    assert any("RESERVE BANK OF INDIA" in c["expected"] for c in failed_checks)


def test_currency_analyze_api_failure_fallback(client, mock_tf_service, tmp_path):
    img_path = tmp_path / "test_error.jpg"
    img_path.write_bytes(b"dummy image content")
    
    # Gemini throws exception
    with patch("app.services.currency_ai.CurrencyAIService._analyze_gemini", side_effect=Exception("API Connection timeout")):
        with patch("app.api.currency.save_upload_file", return_value=img_path):
            with patch("PIL.Image.open") as mock_img:
                mock_img.return_value.verify = MagicMock()
                mock_img.return_value.size = (100, 100)
                
                with open(img_path, "rb") as f:
                    response = client.post(
                        "/api/v1/currency/analyze",
                        files={"file": ("test_error.jpg", f, "image/jpeg")},
                        data={"denomination": "₹500", "note_side": "Front"}
                    )

    assert response.status_code == 200
    data = response.json()["data"]
    # Should fall back to Suspicious with 0 confidence
    assert data["status"] == "Suspicious"
    assert data["confidence"] == 0
    assert "API request failed" in data["reason"]
