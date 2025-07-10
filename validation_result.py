"""
The validation result of a NeoPixel config.
"""

# pylint: disable=too-few-public-methods

class ValidationResult:
    """The result of a validation check. Includes a valid flag and reason why if invalid."""

    valid: bool
    reason: str

    def __init__(self, valid: bool, reason: str):
        self.valid = valid
        self.reason = reason
