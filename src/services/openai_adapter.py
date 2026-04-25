import base64
import requests
from .vision_adapter import VisionAdapter

class OpenAIVisionAdapter(VisionAdapter):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.api_url = "https://api.openai.com/v1/responses"
        from src.utils.config import get_model
        self.model = get_model('openai')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        from src.utils.config import get_debug_mode
        if get_debug_mode():
            print(f"\n=== Using OpenAI Model: {self.model} ===\n")

    def analyze_receipt(self, image_bytes: bytes, prompt: str) -> str:
        try:
            base64_image = base64.b64encode(image_bytes).decode('utf-8')

            payload = {
                "model": self.model,
                "instructions": "You are a helpful assistant that extracts structured data from images of receipts.",
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        ]
                    }
                ],
                "max_output_tokens": 1024
            }

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()

            output = response.json()['output']
            message = next(item for item in output if item['type'] == 'message')
            return message['content'][0]['text']

        except Exception as e:
            raise Exception(f"OpenAI API request failed: {str(e)}") 