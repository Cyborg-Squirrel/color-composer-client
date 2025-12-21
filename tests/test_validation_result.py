"""Tests for ValidationResult class."""

from color_composer_client import ValidationResult


class TestValidationResult:
    """Tests for ValidationResult data class."""

    def test_create_successful_result(self):
        """Test creating a successful validation result."""
        result = ValidationResult(valid=True, reason="")
        
        assert result.valid is True
        assert result.reason == ""

    def test_create_failed_result_with_reason(self):
        """Test creating a failed validation result with error message."""
        reason = "LED count must be greater than 0"
        result = ValidationResult(valid=False, reason=reason)
        
        assert result.valid is False
        assert result.reason == reason
