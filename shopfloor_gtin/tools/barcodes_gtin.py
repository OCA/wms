# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


SUPPORTED_GTIN_LENGTHS = (8, 12, 13, 14)
MAX_GTIN_LENGTH = max(SUPPORTED_GTIN_LENGTHS)


def get_gtin_variants(barcode: str) -> list[str]:
    """Generate all valid GTIN variants (8, 12, 13, 14 digits)."""
    if not is_valid_gtin_barcode(barcode):
        return []

    # Find the unpadded base string by stripping all leading zeros
    unpadded = barcode.lstrip("0")
    unpadded_len = len(unpadded)

    variants = {barcode}

    if unpadded_len in SUPPORTED_GTIN_LENGTHS:
        variants.add(unpadded)

    for target_len in SUPPORTED_GTIN_LENGTHS:
        if target_len > unpadded_len:
            variants.add(unpadded.zfill(target_len))

    return list(variants)


def is_valid_gtin_barcode(barcode: str) -> bool:
    """Validates digit composition, and GTIN checksum."""

    if len(barcode) not in SUPPORTED_GTIN_LENGTHS:
        return False

    if not (barcode.isascii() and barcode.isdigit()):
        return False

    # Normalize GTIN-14 with a leading zero down to GTIN-13
    if len(barcode) == 14 and barcode.startswith("0"):
        barcode = barcode[1:]

    # GTIN Checksum Algorithm (weights alternate 3 and 1 from right to left)
    # The last digit is the checksum digit itself
    digits = [int(char) for char in barcode]
    payload_digits = digits[:-1]
    check_digit = digits[-1]

    # Reversing allows unified index handling across all lengths:
    # Index 0 (1st to the left of checksum) always gets weight 3,
    # index 1 gets weight 1, etc.
    total_sum = sum(
        num * (3 if i % 2 == 0 else 1) for i, num in enumerate(reversed(payload_digits))
    )

    if (total_sum + check_digit) % 10 != 0:
        return False

    return True
