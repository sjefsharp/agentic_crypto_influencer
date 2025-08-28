class Validator:
    @staticmethod
    def validate_length(value: str, min_length: int = 1, max_length: int = 280) -> bool:
        """
        Validates that the string length is within the specified bounds.

        Args:
            value (str): The string to validate.
            min_length (int): Minimum allowed length (inclusive).
            max_length (int): Maximum allowed length (inclusive).

        Returns:
            bool: True if valid, False otherwise.
        """
        length = len(value)
        return min_length <= length <= max_length
