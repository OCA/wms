from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    source_move_line_ids = fields.One2many(
        comodel_name="stock.move.line", inverse_name="location_id", readonly=True
    )
    reserved_move_line_ids = fields.One2many(
        comodel_name="stock.move.line", compute="_compute_reserved_move_lines",
    )

    def is_sublocation_of(self, others):
        """Return True if self is a sublocation of at least one other"""
        self.ensure_one()
        return bool(
            self.env["stock.location"].search_count(
                [("id", "child_of", others.ids), ("id", "=", self.id)]
            )
        )

    def _get_reserved_move_lines(self):
        return self.env["stock.move.line"].search(
            [
                ("location_id", "=", self.id),
                ("product_uom_qty", ">", 0),
                ("state", "not in", ("done", "cancel")),
            ]
        )

    def _compute_reserved_move_lines(self):
        for rec in self:
            rec.update({"reserved_move_line_ids": rec._get_reserved_move_lines()})
