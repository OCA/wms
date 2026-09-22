# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class ShopfloorMenu(models.Model):

    _inherit = "shopfloor.menu"

    stock_issue_strategy = fields.Selection(
        selection_add=[("loss_quantity", "Loss Declaration")],
        ondelete={"loss_quantity": "set default"},
    )

    def _get_stock_issue_strategy_help_entries(self):
        res = super()._get_stock_issue_strategy_help_entries()
        res["loss_quantity"] = _(
            "Lock the quant behind a move of the warehouse's Loss operation "
            "type for investigation, instead of adjusting the actual stock "
            "levels."
        )
        return res
