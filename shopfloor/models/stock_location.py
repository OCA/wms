from odoo import models


class StockLocation(models.Model):
    _inherit = "stock.location"

    def is_sublocation_of(self, other):
        self.ensure_one()
        return bool(
            self.env["stock.location"].search_count(
                [("id", "child_of", other.id), ("id", "=", self.id)]
            )
        )
