import sys
sys.path.append('.')  # Add project root to path
from src.services.vision_service import VisionAPIService
import json

def simple_test():
    # Initialize service
    vision_service = VisionAPIService(use_anthropic=False)
    print(f"\nAPI Key (first 8 chars): {vision_service.api_key[:8]}...")
    print(f"API URL: {vision_service.api_url}")
    print(f"Headers: {json.dumps(vision_service.headers, indent=2)}")
    
    # Load a test image
    with open("test/test_receipt.jpg", "rb") as f:
        image_bytes = f.read()
    print(f"\nImage size: {len(image_bytes)} bytes")
    
    # Try to analyze it
    try:
        # Get the payload before sending
        base64_image = vision_service._encode_image(image_bytes)
        prompt = vision_service._build_prompt()
        print(f"\nPrompt: {prompt}")
        
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image[:50]}..."  # Show start of base64
                            }
                        }
                    ]
                }
            ]
        }
        print(f"\nPayload structure: {json.dumps(payload, indent=2)}")
        
        receipt = vision_service.analyze_receipt(image_bytes)
        print("\nSuccess!")
        print(f"Vendor: {receipt.vendor}")
        print(f"Total: {receipt.total_amount}")
        print(f"Full receipt data: {receipt}")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    simple_test() 