# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# NOTE: This module is deprecated in favor of stock_picking_partner_note.
# Here, we migrate the data from shopfloor.packing.info to stock.picking.note.


def setup_stock_picking_note__packing(env):
    """Create a new packing note type named 'packing'."""

    _logger.info("Create a new picking note type named 'packing'")
    packing_note_type = env["stock.picking.note.type"].search(
        [("name", "=", "packing")], limit=1
    )
    if not packing_note_type:
        packing_note_type = env["stock.picking.note.type"].create({"name": "packing"})
    return packing_note_type


def populate_stock_picking_note__packing(env):
    """Migrate data from shopfloor.packing.info to stock.picking.note of type 'packing'.

    We also update the stock_picking_note_ids of the partners
    based on their existing shopfloor_packing_info_id values."""

    _logger.info(
        "Migrate data from shopfloor.packing.info to stock.picking.note of type 'packing'"
    )
    packing_note_type = setup_stock_picking_note__packing(env)
    existing_packing_infos = env["shopfloor.packing.info"].search([])
    for packing_info in existing_packing_infos:
        note = env["stock.picking.note"].create(
            {
                "name": packing_info.text,
                "note_type_id": packing_note_type.id,
            }
        )
        partner = env["res.partner"].search(
            [("shopfloor_packing_info_id", "=", packing_info.id)], limit=1
        )
        if partner:
            partner.stock_picking_note_ids |= note


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    populate_stock_picking_note__packing(env)
