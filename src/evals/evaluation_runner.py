import os
import pandas as pd
from typing import Dict
from src.services.vision_service import VisionAPIService
from src.utils.config import get_api_key

class EvaluationRunner:
    """Handles individual image evaluations with specific configurations."""
    
    def evaluate_image(self, image_path: str, vendor: str, prompt_method: str) -> pd.Series:
        """
        Evaluate a single image with specified vendor and prompt method.
        
        Args:
            image_path: Path to the image file
            vendor: Vendor to use for evaluation (e.g., 'openai', 'anthropic')
            prompt_method: Prompt method to use (e.g., 'single_prompt')
            
        Returns:
            pd.Series containing the evaluation results
        """
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # Initialize vision service with specified vendor
            api_key = get_api_key(vendor)
            vision_service = VisionAPIService(api_key=api_key, vendor=vendor)
            
            # Process image
            receipt = vision_service.analyze_receipt(image_bytes)
            
            # Convert receipt object to pandas Series
            result = pd.Series({
                'vendor_name': receipt.vendor,
                'invoice_number': receipt.invoice,
                'bill_date': receipt.bill_date,
                'paid_date': receipt.paid_date,
                'payment_method': receipt.payment_method,
                'total_amount': receipt.total_amount,
                'item_type': receipt.item_type,
                'item': receipt.item,
                'project': receipt.project,
                'expense_type': receipt.expense_type,
                'upper_right': receipt.upper_right
            })
            
            return result
            
        except Exception as e:
            raise Exception(f"Evaluation failed: {str(e)}") 