import sys
sys.path.append('.')
from src.services.vision_service import VisionAPIService
import json

def test_vision(image_path: str = "test/test_receipt.jpg"):
    svc = VisionAPIService()
    print(f"Vendor:  {svc.vendor}")
    print(f"Model:   {svc.adapter.model}")
    print(f"API URL: {svc.adapter.api_url}")
    print(f"API Key: {svc.api_key[:8]}...")

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    print(f"\nImage: {image_path} ({len(image_bytes)} bytes)")

    prompt = svc._build_prompt()
    print(f"\nPrompt ({len(prompt)} chars):\n{'-'*40}\n{prompt}\n{'-'*40}")

    print("\nCalling API...")
    try:
        receipt = svc.analyze_receipt(image_bytes)
        print("Success!\n")
        print(json.dumps(receipt.__dict__, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else "test/test_receipt.jpg"
    test_vision(image_path)
