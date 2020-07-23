from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    shopfloor_picking_sequence = fields.Char(
        string="Shopfloor Picking Sequence",
        help="The picking done in Shopfloor scenarios will respect this order. "
        "The sequence is a char so it can be composed of fields such as "
        "'corridor-rack-side-level'. Pay attention to the padding "
        "('09' is before '19', '9' is not). It is recommended to use an"
        " Export then an Import to populate this field using a spreadsheet.",
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
