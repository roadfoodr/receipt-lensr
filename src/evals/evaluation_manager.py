import os
import pandas as pd
from datetime import datetime
from typing import List
from .evaluation_runner import EvaluationRunner
from .evaluation_reporter import EvaluationReporter
from src.utils.config import load_config

class EvaluationManager:
    """Manages the evaluation process for receipt analysis."""
    
    def __init__(self):
        """Initialize the evaluation manager with configuration."""
        self.config = load_config()
        self.eval_dir = self.config.get('eval_images_dir', 'test/eval_images/')
        self.vendors = self.config.get('eval_vendors', ['openai', 'anthropic'])
        self.prompt_methods = self.config.get('eval_prompt_methods', ['single_prompt'])
        
        # Create evaluation directory if it doesn't exist
        os.makedirs(self.eval_dir, exist_ok=True)
        
        self.runner = EvaluationRunner()
        self.reporter = EvaluationReporter()
        
        # Initialize results DataFrame
        self.results_df = pd.DataFrame()
        
    def get_eval_images(self) -> List[str]:
        """Get list of image files from evaluation directory."""
        valid_extensions = {'.jpg', '.jpeg', '.png'}
        image_files = []
        
        try:
            for file in os.listdir(self.eval_dir):
                if os.path.splitext(file)[1].lower() in valid_extensions:
                    image_files.append(os.path.join(self.eval_dir, file))
            return image_files
        except Exception as e:
            print(f"Error reading evaluation directory: {e}")
            return []

    def run_evaluations(self):
        """Run evaluations for all images with all vendor/prompt combinations."""
        images = self.get_eval_images()
        if not images:
            print("No evaluation images found.")
            return
        
        results_list = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for image_path in images:
            print(f"Processing image: {image_path}")
            for vendor in self.vendors:
                for prompt_method in self.prompt_methods:
                    try:
                        # Run evaluation
                        result = self.runner.evaluate_image(
                            image_path=image_path,
                            vendor=vendor,
                            prompt_method=prompt_method
                        )
                        
                        # Add metadata
                        metadata = pd.Series({
                            'image_file': os.path.basename(image_path),
                            'vendor': vendor,
                            'prompt_method': prompt_method,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # Combine metadata and results
                        combined_result = pd.concat([metadata, result])
                        results_list.append(combined_result)
                        
                    except Exception as e:
                        print(f"Error processing {image_path} with {vendor}/{prompt_method}: {e}")
                        # Add error result
                        error_result = pd.Series({
                            'image_file': os.path.basename(image_path),
                            'vendor': vendor,
                            'prompt_method': prompt_method,
                            'timestamp': datetime.now().isoformat(),
                            'error': str(e)
                        })
                        results_list.append(error_result)
        
        # Convert results list to DataFrame
        if results_list:
            self.results_df = pd.DataFrame(results_list)
            output_file = f'output/evals_results_{timestamp}.csv'
            self.reporter.save_results(self.results_df, output_file)
            print(f"Evaluation results saved to: {output_file}") 