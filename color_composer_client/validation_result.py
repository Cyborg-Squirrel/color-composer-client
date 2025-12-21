"""
The validation result of a NeoPixel config.
"""

# pylint: disable=too-few-public-methods


class ValidationResult:
    """Result of a validation check operation.
    
    Attributes:
        valid: True if validation passed, False otherwise.
        reason: Description of validation status or error message if invalid.
    """

    valid: bool
    reason: str

    def __init__(self, valid: bool, reason: str):
        """Initialize a validation result.
        
        Args:
            valid: Whether the validation check passed.
            reason: Human-readable message explaining the result.
        """
        self.valid = valid
        self.reason = reason
