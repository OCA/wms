# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    propagate_to_pickings_chain = fields.Boolean(
        string="Propagate the release channel to pickings chain",
        help="Check this field if you want to propagate the release channel from to the"
        " destination moves.",
    )
