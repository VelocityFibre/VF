#!/usr/bin/env python3
"""
Validate bank routing numbers using ABA check digit algorithm.
"""

import sys
import json
import argparse


def calculate_aba_check_digit(routing_number: str) -> int:
    """
    Calculate ABA routing number check digit.

    Algorithm:
    3 * (D1 + D4 + D7) + 7 * (D2 + D5 + D8) + 1 * (D3 + D6 + D9) mod 10 = 0

    Args:
        routing_number: 9-digit routing number as string

    Returns:
        Expected check digit (last digit)
    """
    if len(routing_number) != 9 or not routing_number.isdigit():
        raise ValueError("Routing number must be exactly 9 digits")

    # Extract first 8 digits
    digits = [int(d) for d in routing_number[:8]]

    # Apply ABA algorithm
    checksum = (
        3 * (digits[0] + digits[3] + digits[6]) +
        7 * (digits[1] + digits[4] + digits[7]) +
        1 * (digits[2] + digits[5])
    )

    # Check digit makes total mod 10 = 0
    check_digit = (10 - (checksum % 10)) % 10

    return check_digit


def validate_routing_number(routing_number: str) -> dict:
    """
    Validate routing number using ABA check digit algorithm.

    Args:
        routing_number: 9-digit routing number

    Returns:
        Validation result dictionary
    """
    try:
        # Clean input (remove spaces, dashes)
        routing_number = routing_number.replace(" ", "").replace("-", "")

        if len(routing_number) != 9:
            return {
                "valid": False,
                "error": "Routing number must be exactly 9 digits",
                "routing_number": routing_number
            }

        if not routing_number.isdigit():
            return {
                "valid": False,
                "error": "Routing number must contain only digits",
                "routing_number": routing_number
            }

        # Calculate expected check digit
        expected_check_digit = calculate_aba_check_digit(routing_number)
        actual_check_digit = int(routing_number[8])

        valid = (expected_check_digit == actual_check_digit)

        return {
            "valid": valid,
            "routing_number": routing_number,
            "check_digit": actual_check_digit,
            "expected_check_digit": expected_check_digit,
            "message": "Routing number is valid" if valid else "Check digit validation failed"
        }

    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "routing_number": routing_number
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate bank routing numbers")
    parser.add_argument("--routing", required=True, help="9-digit routing number")
    args = parser.parse_args()

    result = validate_routing_number(args.routing)
    print(json.dumps(result, indent=2))

    # Exit with non-zero code if invalid
    sys.exit(0 if result.get("valid") else 1)


if __name__ == "__main__":
    main()
