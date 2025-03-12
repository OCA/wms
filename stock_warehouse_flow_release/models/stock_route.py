# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockRoute(models.Model):
    _inherit = "stock.route"

    apply_flow_on = fields.Selection(
        selection_add=[("on_release", "When move is released")]
    )
