import base64
import requests
from .vision_adapter import VisionAdapter

class AnthropicVisionAdapter(VisionAdapter):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-5-sonnet-20241022"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Add debug print
        from src.utils.config import get_debug_mode
        if get_debug_mode():
            print(f"\n=== Using Anthropic Model: {self.model} ===\n")

    def analyze_receipt(self, image_bytes: bytes, prompt: str) -> str:
        try:
            # Convert image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # Construct API payload
            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }],
                "system": "You are a helpful assistant that extracts structured data from images of receipts.",
                "max_tokens": 1024
            }

            # Make API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            # Print response for debugging
            from src.utils.config import get_debug_mode
            if get_debug_mode():
                print(f"\nAPI Response Status: {response.status_code}")
                print(f"API Response: {response.text}\n")
                
            response.raise_for_status()
            
            # Updated response parsing
            response_data = response.json()
            return response_data['content'][0]['text']
                
        except Exception as e:
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"API Response: {response.text}")
            raise Exception(f"Anthropic API request failed: {str(e)}") 