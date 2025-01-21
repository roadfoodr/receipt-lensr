import sys
sys.path.append('.')  # Add project root to path
from src.services.vision_service import VisionAPIService
import json

def test_raw_vision():
    # Initialize service
    vision_service = VisionAPIService(use_anthropic=False)
    
    # Load custom prompt
    with open("test/test_prompt.txt", "r") as f:  # Updated path
        prompt = f.read()
    
    # Load test image
    with open("test/test_receipt.jpg", "rb") as f:  # Updated path
        image_bytes = f.read()
    
    try:
        # Get raw response
        response = vision_service.analyze_image_raw(image_bytes, prompt)
        
        print("\nPrompt used:")
        print("-" * 40)
        print(prompt)
        
        print("\nRaw response:")
        print("-" * 40)
        print(response)
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_raw_vision() 