import asyncio
import json
from app.services.gemini import gemini_service
from app.schemas.fraud import ThreatInputSchema

async def main():
    try:
        input_data = ThreatInputSchema(
            source="WhatsApp",
            text="I am from CBI, your account is blocked. Send 50000 immediately.",
        )
        res = gemini_service.analyze_text(input_data)
        print(json.dumps(res, indent=2))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
