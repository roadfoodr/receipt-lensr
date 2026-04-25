"""Run a raw API call with a custom prompt and print the unprocessed response."""
import sys
sys.path.append('.')
from src.services.vision_service import VisionAPIService

def test_vision_raw(prompt_path: str = None):
    svc = VisionAPIService()
    print(f"Vendor: {svc.vendor}  Model: {svc.adapter.model}\n")

    if prompt_path:
        with open(prompt_path, "r") as f:
            prompt = f.read()
    else:
        prompt = svc._build_prompt()

    with open("test/test_receipt.jpg", "rb") as f:
        image_bytes = f.read()

    print(f"Prompt:\n{'-'*40}\n{prompt}\n{'-'*40}\n")

    try:
        response = svc.analyze_image_raw(image_bytes, prompt)
        print(f"Raw response:\n{'-'*40}\n{response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    prompt_path = sys.argv[1] if len(sys.argv) > 1 else None
    test_vision_raw(prompt_path)
