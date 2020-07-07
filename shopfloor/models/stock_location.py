from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    shopfloor_picking_sequence = fields.Integer(
        string="Shopfloor Picking Sequence",
        default=0,
        help="The picking done in Shopfloor scenarios will respect this order.",
    )
    source_move_line_ids = fields.One2many(
        comodel_name="stock.move.line", inverse_name="location_id", readonly=True
    )
    reserved_move_line_ids = fields.One2many(
        comodel_name="stock.move.line", compute="_compute_reserved_move_lines",
    )

    def is_sublocation_of(self, others):
        """Return True if self is a sublocation of at least one other"""
        self.ensure_one()
        # Efficient way to verify that the current location is
        # below one of the other location without using SQL.
        return any(self.parent_path.startswith(other.parent_path) for other in others)

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
