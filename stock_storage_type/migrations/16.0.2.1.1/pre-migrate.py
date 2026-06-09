# Copyright 2026 ACSONE SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import logging

from odoo.tools import sql

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if sql.column_exists(cr, "stock_location", "has_potential_product_mix_exception"):
        return

    _logger.info("Adding potential mix exception columns on stock_location")
    sql.create_column(
        cr, "stock_location", "has_potential_product_mix_exception", "boolean"
    )
    sql.create_column(
        cr, "stock_location", "has_potential_lot_mix_exception", "boolean"
    )
