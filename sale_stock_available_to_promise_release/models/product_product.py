# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_next_replenishment_date(self):
        self.ensure_one()
        move_line = self.env["stock.move"].search(
            [
                ("product_id", "=", self.id),
                ("state", "not in", ["done", "cancel"]),
                ("picking_type_id.code", "=", "incoming"),
            ],
            limit=1,
            order="date_expected asc",
        )
        return move_line and move_line.date_expected or False
