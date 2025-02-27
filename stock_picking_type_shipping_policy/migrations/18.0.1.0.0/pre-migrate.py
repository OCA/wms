# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging

from odoo import tools

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    migrate_stock_picking_type_shipping_policy(cr)


def migrate_stock_picking_type_shipping_policy(cr):
    _logger.info("Create 'stock_picking_type.force_move_type' column...")
    tools.sql.create_column(cr, "stock_picking_type", "force_move_type", "boolean")
    _logger.info("Update operation types configuration...")
    # Odoo 18.0 comes with a new '<stock.picking.type>.move_type' field sets
    # by default to 'direct' (= As soon as possible).
    # If the current module is installed, we want this field sets with the
    # value that was configured in old field 'shipping_policy'.
    queries = [
        """
            UPDATE stock_picking_type
            SET force_move_type=true, move_type='direct'
            WHERE shipping_policy='force_as_soon_as_possible';
        """,
        """
            UPDATE stock_picking_type
            SET force_move_type=true, move_type='one'
            WHERE shipping_policy='force_all_products_ready';
        """,
    ]
    for query in queries:
        cr.execute(query)
