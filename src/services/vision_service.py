# src/services/vision_service.py

import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import requests
import json
import os
from .vision_adapter import Receipt
from .openai_adapter import OpenAIVisionAdapter
from .anthropic_adapter import AnthropicVisionAdapter

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
    item_type: Optional[str] = None
    item: Optional[str] = None
    project: Optional[str] = None
    expense_type: Optional[str] = None
    upper_right: Optional[str] = None

class VisionAPIService:
    def __init__(self, api_key: str = None, vendor: str = None):
        """Initialize the Vision API service"""
        from src.utils.config import get_api_key, get_vendor
        
        # Get vendor from config if not provided
        self.vendor = vendor or get_vendor()
        if not self.vendor:
            raise ValueError("No vendor specified. Please check your config.json")
            
        # Get API key for the specified vendor
        self.api_key = api_key or get_api_key(self.vendor)
        if not self.api_key:
            raise ValueError(f"No API key available for {self.vendor}. Please check your config.json")
            
        # Initialize the appropriate adapter based on vendor
        self.adapter = self._create_adapter()
        
        # Initialize corrections
        self.corrections = ""
        self.corrections = self._load_corrections()
        
    def _create_adapter(self):
        """Create the appropriate adapter based on vendor"""
        if self.vendor.lower() == "anthropic":
            return AnthropicVisionAdapter(self.api_key)
        elif self.vendor.lower() == "openai":
            return OpenAIVisionAdapter(self.api_key)
        elif self.vendor.lower() == "gemini":
            raise NotImplementedError("Gemini adapter not yet implemented")
        else:
            raise ValueError(f"Unsupported vendor: {self.vendor}")

    def _load_corrections(self) -> str:
        """Load corrections from corrections.txt as raw text"""
        corrections_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'corrections.txt')
        corrections = ""
        
        try:
            if os.path.exists(corrections_path):
                with open(corrections_path, 'r') as f:
                    corrections = f.read()
                    
            # Print corrections if debug mode is enabled
            from src.utils.config import get_debug_mode
            if get_debug_mode():
                print("\n=== LOADED CORRECTIONS ===")
                print(corrections)
                print("=========================\n")
                    
            return corrections
        except Exception as e:
            print(f"Warning: Failed to load corrections: {e}")
            return ""

    def _build_prompt(self, previous_corrections: Optional[str] = None) -> str:
        """Build the prompt for receipt analysis"""
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'receipt_analysis.txt')
        with open(prompt_path, 'r') as f:
            prompt = f.read()

        if previous_corrections:
            correction_preamble = '''
            \n\nAfter determining the values for the fields, please apply the following corrections.  These are very important, and should be applied to all receipts exactly as written:
            \n'''
            prompt += correction_preamble + previous_corrections
            
        return prompt

    def analyze_receipt(self, image_bytes: bytes, previous_corrections: Optional[str] = None) -> Receipt:
        """Analyze a receipt image using the Vision API"""
        try:
            # Use stored corrections if none provided
            if previous_corrections is None:
                previous_corrections = self.corrections
            
            # Get the prompt for receipt analysis
            prompt = self._build_prompt(previous_corrections)
            
            # Print prompt in debug mode
            from src.utils.config import get_debug_mode
            if get_debug_mode():
                print("\n=== PROMPT ===")
                print(prompt)
                print("=============\n")
            
            # Use the adapter to analyze the image
            result = self.adapter.analyze_receipt(image_bytes, prompt)
            
            # Parse the response into a Receipt object
            return self.adapter.parse_response(result)
            
        except Exception as e:
            raise Exception(f"Receipt analysis failed: {str(e)}")

    def analyze_image_raw(self, image_bytes: bytes, prompt: str) -> str:
        """Analyze an image with a custom prompt and return raw response"""
        return self.adapter.analyze_receipt(image_bytes, prompt)

    def add_correction(self, correction: str):
        """Add a new correction to memory"""
        self.corrections += "\n" + correction