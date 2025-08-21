# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    unrelease_on_unavailable_to_promise = fields.Boolean(
        string="Unrelease on unavailable to promise",
        help="If checked, when a move becomes waiting for availabitlity and "
        "is the result of a release, the original move is unreleased ",
    )
