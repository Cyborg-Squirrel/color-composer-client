"""
The validation result of a NeoPixel config.
"""

class ValidationResult:
    valid: bool
    reason: str

    def __init__(self, valid: bool, reason: str):
        self.valid = valid
        self.reason = reason
