import os
import pandas as pd
from typing import List, Dict

class EvaluationReporter:
    """Handles reporting and saving evaluation results."""
    
    def __init__(self):
        """Initialize the evaluation reporter."""
        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)
        
        # Define column order
        self.column_order = [
            'image_file', 'vendor', 'prompt_method', 'timestamp',
            'vendor_name', 'invoice_number', 'bill_date', 'paid_date',
            'payment_method', 'total_amount', 'item_type', 'item',
            'project', 'expense_type', 'upper_right', 'error'
        ]
    
    def save_results(self, results_df: pd.DataFrame, output_file: str):
        """
        Save evaluation results to CSV file.
        
        Args:
            results_df: DataFrame containing evaluation results
            output_file: Path to output CSV file
        """
        try:
            # Reorder columns, keeping any additional columns at the end
            existing_columns = [col for col in self.column_order if col in results_df.columns]
            additional_columns = [col for col in results_df.columns if col not in self.column_order]
            final_columns = existing_columns + additional_columns
            
            # Reorder and save to CSV
            results_df[final_columns].to_csv(output_file, index=False)
            
            # Generate summary statistics
            self._generate_summary(results_df, output_file)
            
        except Exception as e:
            print(f"Error saving results to CSV: {e}")
    
    def _generate_summary(self, df: pd.DataFrame, output_file: str):
        """Generate summary statistics for the evaluation results."""
        try:
            summary_file = output_file.replace('.csv', '_summary.txt')
            
            with open(summary_file, 'w') as f:
                f.write("=== Evaluation Summary ===\n\n")
                
                # Overall statistics
                f.write(f"Total evaluations: {len(df)}\n")
                f.write(f"Images processed: {df['image_file'].nunique()}\n")
                f.write(f"Vendors used: {', '.join(df['vendor'].unique())}\n")
                f.write(f"Prompt methods: {', '.join(df['prompt_method'].unique())}\n\n")
                
                # Error statistics
                error_count = df['error'].notna().sum()
                f.write(f"Successful evaluations: {len(df) - error_count}\n")
                f.write(f"Failed evaluations: {error_count}\n\n")
                
                # Vendor performance
                f.write("=== Vendor Performance ===\n")
                vendor_stats = df.groupby('vendor')['error'].notna().agg(['count', 'sum'])
                vendor_stats['success_rate'] = (1 - vendor_stats['sum'] / vendor_stats['count']) * 100
                f.write(vendor_stats.to_string())
                
            print(f"Summary statistics saved to: {summary_file}")
            
        except Exception as e:
            print(f"Error generating summary statistics: {e}") 