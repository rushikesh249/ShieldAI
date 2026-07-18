import sys
import asyncio
from app.services.gemini import gemini_service
from app.schemas.fraud import ThreatInputSchema
import json

def main():
    text = "Earn ₹5000 daily working from home! No experience required. Just like our YouTube videos and get paid instantly. Pay a small refundable registration fee of ₹999 to start getting tasks. WhatsApp us now to start earning."
    input_data = ThreatInputSchema(
        source="WhatsApp",
        text=text
    )
    result = gemini_service.analyze_text(input_data)
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
