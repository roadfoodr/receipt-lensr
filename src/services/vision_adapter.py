from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import json

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

class VisionAdapter(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def analyze_receipt(self, image_bytes: bytes, prompt: str) -> str:
        """
        Analyze receipt image using the vision API
        Args:
            image_bytes: Raw image bytes
            prompt: Analysis prompt/instructions
        Returns:
            Raw JSON response string from the vision API
        """
        pass

    def parse_response(self, response: str) -> Receipt:
        """
        Parse the API response into a Receipt object
        Can be overridden by concrete adapters if needed
        """
        # Clean up markdown code blocks if present
        if response.startswith('```'):
            response = response.split('```')[1]
            if response.startswith('json'):
                response = response[4:]
            response = response.strip()
        
        # Parse JSON into Receipt object
        data = json.loads(response)
        return Receipt(
            vendor=data.get('vendor', 'not found'),
            invoice=data.get('invoice', 'not found'),
            bill_date=data.get('bill_date', 'not found'),
            paid_date=data.get('paid_date', 'not found'),
            payment_method=data.get('payment_method', 'not found'),
            total_amount=data.get('total_amount', 'not found'),
            item_type=data.get('item_type', 'not found'),
            item=data.get('item', 'not found'),
            project=data.get('project', 'not found'),
            expense_type=data.get('expense_type', 'not found'),
            upper_right=data.get('upper_right', 'not found')
        ) 