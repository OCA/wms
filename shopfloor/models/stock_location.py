from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    source_move_line_ids = fields.One2many(
        comodel_name="stock.move.line", inverse_name="location_id", readonly=True
    )

    def is_sublocation_of(self, other):
        self.ensure_one()
        return bool(
            self.env["stock.location"].search_count(
                [("id", "child_of", other.id), ("id", "=", self.id)]
            )
        )
