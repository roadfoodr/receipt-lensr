from dataclasses import dataclass
from typing import Optional

@dataclass
class CorrectionRule:
    field: str
    original_value: str
    corrected_value: str
    vendor_context: Optional[str] = None

class CorrectionFormatter:
    @staticmethod
    def format_rule(rule: CorrectionRule) -> str:
        """Format a correction rule into a standardized string format"""
        if rule.field == 'vendor':
            correction = f'When vendor is "{rule.original_value}", change vendor to "{rule.corrected_value}"'
        else:
            correction = (f'When vendor is "{rule.vendor_context}" and {rule.field} is '
                        f'"{rule.original_value}", change {rule.field} to "{rule.corrected_value}"')
        
        # Ensure correction starts with exactly one "- "
        return f"- {correction}"

    @staticmethod
    def parse_rule(rule_text: str) -> CorrectionRule:
        """Parse a correction rule string back into a CorrectionRule object"""
        # Add parsing logic here if needed
        pass 