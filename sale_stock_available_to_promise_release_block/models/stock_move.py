# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    unblocked_by_order_id = fields.Many2one(
        comodel_name="sale.order",
        ondelete="set null",
        string="Unblocked by order",
        readonly=True,
        index=True,
    )
