# Patch for get_numeric_input to support min_val and max_val

def get_numeric_input(prompt: str, allow_decimal: bool = True, min_val=None, max_val=None, error_message: str = None) -> str:
    """
    Get numeric input from user with optional range validation

    Args:
        prompt: Prompt to display
        allow_decimal: Whether to allow decimal numbers
        min_val: Minimum value allowed (optional)
        max_val: Maximum value allowed (optional)
        error_message: Custom error message for range validation

    Returns:
        Numeric string or None if invalid
    """
    while True:
        user_input = input(f"\n{prompt}: ").strip()

        if not user_input:
            print("Input cannot be empty. Please try again.\n")
            continue

        try:
            if allow_decimal:
                num_val = float(user_input)
            else:
                num_val = int(user_input)

            # Validate range if specified
            if min_val is not None and num_val < min_val:
                err_msg = error_message or f"Please enter a value >= {min_val}"
                print(f"{err_msg}\n")
                continue

            if max_val is not None and num_val > max_val:
                err_msg = error_message or f"Please enter a value <= {max_val}"
                print(f"{err_msg}\n")
                continue

            return user_input
        except ValueError:
            print(
                f"Invalid number. Please enter a valid "
                f"{'decimal' if allow_decimal else 'integer'} number.\n"
            )
