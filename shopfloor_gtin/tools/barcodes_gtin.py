# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from biip import EncodeError, ParseError
from biip.gtin import Gtin

_logger = logging.getLogger(__name__)


def get_gtin_variants(barcode: str) -> list[str]:
    """Generate all valid GTIN variants (8, 12, 13, 14 digits)."""
    gtin_barcode = parse_gtin(barcode)
    if not gtin_barcode:
        return []

    variants = {barcode}

    format_methods = (
        gtin_barcode.as_gtin_8,
        gtin_barcode.as_gtin_12,
        gtin_barcode.as_gtin_13,
        gtin_barcode.as_gtin_14,
    )
    for format_method in format_methods:
        try:
            variants.add(format_method())
        except EncodeError:
            _logger.debug(
                "Failed to convert barcode %s using %s",
                barcode,
                format_method.__name__,
            )

    return list(variants)


def parse_gtin(barcode: str) -> Gtin | None:
    try:
        return Gtin.parse(barcode)
    except ParseError:
        return None
