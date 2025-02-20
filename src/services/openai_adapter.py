import base64
import requests
from .vision_adapter import VisionAdapter

class OpenAIVisionAdapter(VisionAdapter):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o-mini"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Add debug print
        from src.utils.config import get_debug_mode
        if get_debug_mode():
            print(f"\n=== Using OpenAI Model: {self.model} ===\n")

    def analyze_receipt(self, image_bytes: bytes, prompt: str) -> str:
        try:
            # Convert image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # Construct API payload
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1024
            }

            # Make API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            return response.json()['choices'][0]['message']['content']
                
        except Exception as e:
            raise Exception(f"OpenAI API request failed: {str(e)}") 