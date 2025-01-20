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
    date: Optional[datetime]
    vendor: str
    total_amount: Optional[float]
    items: List[ReceiptItem]
    category: Optional[str] = None
    tax_amount: Optional[float] = None
    
class VisionAPIService:
    def __init__(self, api_key: str = None, use_anthropic: bool = False):
        """Initialize the Vision API service
        
        Args:
            api_key: API key for either OpenAI or Anthropic. If None, will load from config
            use_anthropic: If True, use Claude Vision API, otherwise use OpenAI
            
        Raises:
            ValueError: If no API key is available or configuration is invalid
        """
        from src.utils.config import get_api_key
        
        # If no API key provided, try to load from config
        self.api_key = api_key or get_api_key(use_anthropic)
        if not self.api_key:
            raise ValueError("No API key available. Please check your config.json")
            
        self.use_anthropic = use_anthropic
        # print(f"api_key: {self.api_key}")
        
        if use_anthropic:
            self.api_url = "https://api.anthropic.com/v1/messages"
            self.headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        else:
            self.api_url = "https://api.openai.com/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

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
        """Analyze a receipt image using the Vision API
        
        Args:
            image_bytes: Raw bytes of the receipt image
            previous_corrections: Optional dictionary of previous corrections for learning
            
        Returns:
            Receipt object with extracted information
            
        Raises:
            Exception: If API call fails or response parsing fails
        """
        base64_image = self._encode_image(image_bytes)
        prompt = self._build_prompt(previous_corrections)
        
        if self.use_anthropic:
            payload = {
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }],
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1024
            }
        else:
            payload = {
                "model": "gpt-4o-mini",
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
            
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            # Parse response
            if self.use_anthropic:
                result = response.json()['content'][0]['text']
            else:
                result = response.json()['choices'][0]['message']['content']
            
            print(f"result: {result}")

            # Clean up markdown code blocks if present 
            if result.startswith('```'):
                result = result.split('```')[1] # Get content between markers
                if result.startswith('json'): # Remove json language identifier
                    result = result[4:]
                    result = result.strip() # Remove any extra whitespace

            # Parse the JSON response into our dataclass
            data = json.loads(result)
            
            # Convert items to ReceiptItem objects
            items = [ReceiptItem(**item) for item in data.get('items', [])]
            
            # Create Receipt object with proper type conversion
            receipt = Receipt(
                date=datetime.fromisoformat(data['date']) if data['date'] != "not found" else None,
                vendor=data['vendor'],
                total_amount=float(data['total_amount']) if data['total_amount'] != "not found" else None,
                items=items,
                category=data.get('category'),
                tax_amount=float(data['tax_amount']) if data['tax_amount'] != "not found" else None
            )
            
            return receipt
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise Exception(f"Failed to parse API response: {str(e)}")

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