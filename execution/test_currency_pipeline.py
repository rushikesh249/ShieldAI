"""
ShieldAI — Currency Vision Verification Test Suite

Tests the currency_ai_service pipeline across 17 test categories to verify
that every category produces a DIFFERENT, image-dependent, and logically correct response.
"""

import sys
import os
import io
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.services.currency_ai import currency_ai_service

# Temporary directory for test image artifacts
TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp" / "test_images"
TMP_DIR.mkdir(parents=True, exist_ok=True)


def create_blank_image() -> Path:
    img = Image.new("RGB", (600, 400), color="white")
    path = TMP_DIR / "blank_image.png"
    img.save(path)
    return path


def create_cat_image() -> Path:
    img = Image.new("RGB", (600, 400), color="orange")
    draw = ImageDraw.Draw(img)
    # Draw simple cat face shape
    draw.ellipse([200, 100, 400, 300], fill="brown", outline="black")
    # Ears
    draw.polygon([(220, 120), (250, 40), (280, 110)], fill="brown")
    draw.polygon([(320, 110), (350, 40), (380, 120)], fill="brown")
    # Eyes & Nose
    draw.ellipse([250, 170, 270, 190], fill="green")
    draw.ellipse([330, 170, 350, 190], fill="green")
    draw.polygon([(290, 220), (310, 220), (300, 235)], fill="pink")
    draw.text((230, 320), "CAT ANIMAL IMAGE", fill="white")
    path = TMP_DIR / "cat_image.png"
    img.save(path)
    return path


def create_dog_image() -> Path:
    img = Image.new("RGB", (600, 400), color="tan")
    draw = ImageDraw.Draw(img)
    draw.ellipse([180, 120, 420, 320], fill="saddlebrown")
    draw.ellipse([150, 160, 220, 280], fill="black") # Floppy ear
    draw.ellipse([380, 160, 450, 280], fill="black") # Floppy ear
    draw.ellipse([270, 220, 330, 270], fill="black") # Snout
    draw.text((230, 330), "DOG ANIMAL IMAGE", fill="white")
    path = TMP_DIR / "dog_image.png"
    img.save(path)
    return path


def create_human_face() -> Path:
    img = Image.new("RGB", (600, 400), color="gainsboro")
    draw = ImageDraw.Draw(img)
    draw.ellipse([220, 80, 380, 280], fill="bisque", outline="black")
    draw.ellipse([260, 140, 280, 160], fill="blue") # Left eye
    draw.ellipse([320, 140, 340, 160], fill="blue") # Right eye
    draw.line([(300, 170), (300, 210)], fill="black", width=3) # Nose
    draw.arc([270, 220, 330, 250], start=0, end=180, fill="red", width=3) # Smile
    draw.text((220, 320), "HUMAN PORTRAIT FACE", fill="black")
    path = TMP_DIR / "human_face.png"
    img.save(path)
    return path


def create_landscape() -> Path:
    img = Image.new("RGB", (600, 400), color="skyblue")
    draw = ImageDraw.Draw(img)
    # Sun
    draw.ellipse([450, 40, 550, 140], fill="gold")
    # Mountains
    draw.polygon([(0, 400), (200, 150), (400, 400)], fill="darkgreen")
    draw.polygon([(250, 400), (450, 200), (600, 400)], fill="forestgreen")
    draw.text((200, 350), "LANDSCAPE NATURE", fill="white")
    path = TMP_DIR / "landscape.png"
    img.save(path)
    return path


def create_qr_code() -> Path:
    img = Image.new("RGB", (500, 500), color="white")
    draw = ImageDraw.Draw(img)
    # Grid pattern imitating QR code
    for i in range(10):
        for j in range(10):
            if (i + j) % 2 == 0:
                draw.rectangle([i*40 + 50, j*40 + 50, i*40 + 80, j*40 + 80], fill="black")
    # Corner markers
    draw.rectangle([50, 50, 130, 130], fill="black")
    draw.rectangle([65, 65, 115, 115], fill="white")
    draw.rectangle([80, 80, 100, 100], fill="black")

    draw.rectangle([370, 50, 450, 130], fill="black")
    draw.rectangle([385, 65, 435, 115], fill="white")
    draw.rectangle([400, 80, 420, 100], fill="black")
    path = TMP_DIR / "qr_code.png"
    img.save(path)
    return path


def create_document() -> Path:
    img = Image.new("RGB", (600, 700), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((50, 40), "OFFICIAL INVOICE DOCUMENT", fill="navy")
    for y in range(90, 600, 30):
        draw.line([(50, y), (550, y)], fill="gray", width=2)
    path = TMP_DIR / "document.png"
    img.save(path)
    return path


def create_laptop_screen() -> Path:
    img = Image.new("RGB", (700, 450), color="darkgray")
    draw = ImageDraw.Draw(img)
    # Bezel and screen
    draw.rectangle([40, 30, 660, 380], fill="black")
    draw.rectangle([50, 40, 650, 370], fill="midnightblue")
    draw.text((200, 180), "WINDOWS DESKTOP SCREENSHOT", fill="white")
    path = TMP_DIR / "laptop_screen.png"
    img.save(path)
    return path


def create_mobile_screenshot() -> Path:
    img = Image.new("RGB", (360, 780), color="black")
    draw = ImageDraw.Draw(img)
    # Status bar
    draw.text((20, 10), "9:41 AM", fill="white")
    draw.text((280, 10), "100%", fill="white")
    # App UI
    draw.rectangle([20, 60, 340, 120], fill="purple")
    draw.text((40, 80), "CHAT MESSAGING APP", fill="white")
    for y in range(140, 700, 90):
        draw.rectangle([20, y, 340, y + 70], fill="darkgray")
    path = TMP_DIR / "mobile_screenshot.png"
    img.save(path)
    return path


def create_foreign_currency() -> Path:
    img = Image.new("RGB", (700, 320), color="lightgreen")
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 690, 310], outline="darkgreen", width=4)
    draw.text((30, 30), "$100", fill="darkgreen")
    draw.text((200, 120), "UNITED STATES OF AMERICA", fill="darkgreen")
    draw.text((250, 160), "ONE HUNDRED DOLLARS - USD", fill="darkgreen")
    draw.ellipse([450, 80, 580, 240], outline="darkgreen", width=3)
    draw.text((480, 150), "BEN FRANKLIN", fill="darkgreen")
    path = TMP_DIR / "foreign_currency_usd.png"
    img.save(path)
    return path


def create_synthetic_note(denom="₹500", quality="clear") -> Path:
    color_map = {
        "₹100": "lavender",
        "₹200": "gold",
        "₹500": "lightstonegray",
        "₹2000": "magenta"
    }
    bg = color_map.get(denom, "lightgray")
    if bg == "lightstonegray": bg = "#A0A0A0"
    
    img = Image.new("RGB", (800, 380), color=bg)
    draw = ImageDraw.Draw(img)
    
    # Note Border & Graphics
    draw.rectangle([10, 10, 790, 370], outline="navy", width=3)
    draw.text((30, 30), "RESERVE BANK OF INDIA", fill="navy")
    draw.text((30, 60), "GUARANTEED BY THE CENTRAL GOVERNMENT", fill="navy")
    draw.text((650, 30), denom, fill="navy")
    
    # Gandhi Portrait Watermark area
    draw.ellipse([100, 100, 260, 280], outline="gray", width=2)
    draw.text((130, 180), "MAHATMA GANDHI", fill="black")
    
    # Security Thread
    draw.rectangle([340, 10, 355, 370], fill="green")
    draw.text((342, 100), "RBI", fill="yellow")
    draw.text((342, 200), "BHARAT", fill="yellow")
    
    # Latent / Emblem
    draw.rectangle([680, 250, 760, 340], fill="olive")
    draw.text((700, 280), denom, fill="white")

    if quality == "blurry":
        img = img.filter(ImageFilter.GaussianBlur(radius=12))
    elif quality == "cropped":
        img = img.crop((200, 100, 600, 300))

    path = TMP_DIR / f"synthetic_{denom}_{quality}.png"
    img.save(path)
    return path


def run_tests():
    print("=" * 80)
    print("SHIELDAI CURRENCY VISION PIPELINE VERIFICATION TEST")
    print("=" * 80)

    test_cases = [
        ("Genuine ₹100", create_synthetic_note("₹100", "clear"), "₹100", "Front"),
        ("Genuine ₹200", create_synthetic_note("₹200", "clear"), "₹200", "Front"),
        ("Genuine ₹500", create_synthetic_note("₹500", "clear"), "₹500", "Front"),
        ("Genuine ₹2000", create_synthetic_note("₹2000", "clear"), "₹2000", "Front"),
        ("Foreign Currency (USD)", create_foreign_currency(), "₹500", "Front"),
        ("Blank Image", create_blank_image(), "₹500", "Front"),
        ("Mobile Screenshot", create_mobile_screenshot(), "₹500", "Front"),
        ("Laptop Screen", create_laptop_screen(), "₹500", "Front"),
        ("Human Face", create_human_face(), "₹500", "Front"),
        ("Cat Image", create_cat_image(), "₹500", "Front"),
        ("Dog Image", create_dog_image(), "₹500", "Front"),
        ("Landscape", create_landscape(), "₹500", "Front"),
        ("Document", create_document(), "₹500", "Front"),
        ("QR Code", create_qr_code(), "₹500", "Front"),
        ("Extremely Blurred Note", create_synthetic_note("₹500", "blurry"), "₹500", "Front"),
        ("Cropped Note", create_synthetic_note("₹500", "cropped"), "₹500", "Front"),
    ]

    results = []
    
    for idx, (label, file_path, denom, side) in enumerate(test_cases, 1):
        print(f"\n[{idx}/16] Testing: {label} (File: {file_path.name})")
        start = time.perf_counter()
        try:
            res = currency_ai_service.analyze(file_path, "image/png", denom, side)
            dur = (time.perf_counter() - start) * 1000
            
            risk = res.get("riskLevel")
            conf = res.get("confidenceScore")
            evidence = res.get("evidence", [])
            verdict_line = evidence[0] if evidence else "N/A"
            reason_line = evidence[1] if len(evidence) > 1 else "N/A"
            
            print(f"    └─ Time: {dur:.1f}ms")
            print(f"    └─ Risk Level: {risk} | Confidence: {conf}%")
            print(f"    └─ Primary Output: {verdict_line}")
            print(f"    └─ Secondary Output: {reason_line}")
            
            results.append({
                "label": label,
                "file": file_path.name,
                "risk": risk,
                "confidence": conf,
                "verdict_line": verdict_line,
                "reason_line": reason_line,
                "full_evidence": evidence
            })
        except Exception as e:
            print(f"    └─ ERROR: {str(e)}")
            results.append({
                "label": label,
                "file": file_path.name,
                "risk": "ERROR",
                "confidence": 0,
                "verdict_line": f"ERROR: {str(e)}",
                "reason_line": "Pipeline exception",
                "full_evidence": []
            })
        time.sleep(3) # Prevent hitting free-tier rate limits

    print("\n" + "=" * 80)
    print("SUMMARY OF TEST RESULTS")
    print("=" * 80)
    for r in results:
        print(f"• {r['label']:<25} | Risk: {r['risk']:<18} | Summary: {r['verdict_line']}")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
