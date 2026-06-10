# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockRoute(models.Model):
    _inherit = "stock.route"

    autoblock_release_on_backorder = fields.Selection(
        string="Auto-block Release on Backorders",
        selection=[
            ("never", "Never"),
            ("always", "Always"),
            ("single_customer_outgoing_move", "On single OUT move for customer"),
        ],
        default="never",
        required=True,
    )
