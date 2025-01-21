# src/services/vision_service.py

import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import requests
import json
import os

@dataclass
class ReceiptItem:
    description: str
    amount: float
    quantity: Optional[float] = None

@dataclass
class Receipt:
    vendor: Optional[str] = None
    invoice: Optional[str] = None
    bill_date: Optional[str] = None
    paid_date: Optional[str] = None
    payment_method: Optional[str] = None
    total_amount: Optional[str] = None
    item: Optional[str] = None
    project: Optional[str] = None
    upper_right: Optional[str] = None

class VisionAPIService:
    def __init__(self, api_key: str = None, use_anthropic: bool = False):
        """Initialize the Vision API service"""
        from src.utils.config import get_api_key
        
        self.api_key = api_key or get_api_key(use_anthropic)
        if not self.api_key:
            raise ValueError("No API key available. Please check your config.json")
            
        self.use_anthropic = use_anthropic
        self._setup_api_config()

    def _setup_api_config(self):
        """Set up API configuration based on service type"""
        if self.use_anthropic:
            self.api_url = "https://api.anthropic.com/v1/messages"
            self.model = "claude-3-haiku-20240307"
            self.headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        else:
            self.api_url = "https://api.openai.com/v1/chat/completions"
            self.model = "gpt-4o-mini"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

    def _create_payload(self, prompt: str, image_base64: str) -> dict:
        """Create API payload based on service type"""
        if self.use_anthropic:
            return {
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64
                            }
                        }
                    ]
                }],
                "model": self.model,
                "max_tokens": 1024
            }
        else:
            return {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1024
            }

    def _make_request(self, payload: dict) -> str:
        """Make API request and extract response text"""
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        if self.use_anthropic:
            return response.json()['content'][0]['text']
        else:
            return response.json()['choices'][0]['message']['content']

    def _encode_image(self, image_bytes: bytes) -> str:
        """Convert image bytes to base64 string"""
        return base64.b64encode(image_bytes).decode('utf-8')
        
    def _build_prompt(self, previous_corrections: Optional[dict] = None) -> str:
        """Build the prompt for receipt analysis"""
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'receipt_analysis.txt')
        with open(prompt_path, 'r') as f:
            prompt = f.read()

        if previous_corrections:
            prompt += "\nPrevious corrections to consider: " + json.dumps(previous_corrections)
                
        return prompt

    def analyze_receipt(self, image_bytes: bytes, previous_corrections: Optional[dict] = None) -> Receipt:
        """Analyze a receipt image using the Vision API"""
        try:
            # Get the prompt for receipt analysis
            prompt = self._build_prompt(previous_corrections)
            
            # Use analyze_image_raw to get the response
            result = self.analyze_image_raw(image_bytes, prompt)
            
            # Clean up markdown code blocks if present
            if result.startswith('```'):
                result = result.split('```')[1]
                if result.startswith('json'):
                    result = result[4:]
                result = result.strip()
            
            # Parse the JSON response into our dataclass
            data = json.loads(result)
            
            return Receipt(
                vendor=data.get('vendor', 'not found'),
                invoice=data.get('invoice', 'not found'),
                bill_date=data.get('bill_date', 'not found'),
                paid_date=data.get('paid_date', 'not found'),
                payment_method=data.get('payment_method', 'not found'),
                total_amount=data.get('total_amount', 'not found'),
                item=data.get('item', 'not found'),
                project=data.get('project', 'not found'),
                upper_right=data.get('upper_right', 'not found')
            )
            
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")

    def handle_correction(self, original: Receipt, corrected: Receipt) -> dict:
        """Process corrections to improve future extractions
        
        Args:
            original: Original Receipt object from API
            corrected: Corrected Receipt object from user
            
        Returns:
            Dictionary of learning points for future prompts
        """
        corrections = {}
        
        # Compare fields and identify corrections
        if original.vendor != corrected.vendor:
            corrections['vendor'] = f"When the receipt shows '{original.vendor}', it should be interpreted as '{corrected.vendor}'"
            
        if original.total_amount != corrected.total_amount:
            corrections['total_amount'] = f"Pay special attention to decimal places and currency symbols"
            
        if original.category != corrected.category:
            corrections['category'] = f"Purchases from {corrected.vendor} should be categorized as {corrected.category}"
            
        return corrections

    def analyze_image_raw(self, image_bytes: bytes, prompt: str) -> str:
        """Analyze an image with a custom prompt and return raw response"""
        try:
            base64_image = self._encode_image(image_bytes)
            payload = self._create_payload(prompt, base64_image)
            return self._make_request(payload)
                
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")