# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models
from odoo.tools.float_utils import float_compare


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
        comodel_name="stock.move.line",
        compute="_compute_reserved_move_lines",
    )

    def _get_reserved_move_lines(self):
        return self.env["stock.move.line"].search(
            [
                ("location_id", "child_of", self.id),
                ("product_uom_qty", ">", 0),
                ("state", "not in", ("done", "cancel")),
            ]
        )

    def _compute_reserved_move_lines(self):
        for rec in self:
            rec.update({"reserved_move_line_ids": rec._get_reserved_move_lines()})

    def planned_qty_in_location_is_empty(self, move_lines=None):
        """Return if a location will be empty when move lines will be confirmed

        Used for the "zero check". We need to know if a location is empty, but since
        we set the move lines to "done" only at the end of the unload workflow, we
        have to look at the qty_done of the move lines from this location.

        With `move_lines` we can force the use of the given move lines for the check.
        This allows to know that the location will be empty if we process only
        these move lines.
        """
        self.ensure_one()
        quants = self.env["stock.quant"].search(
            [("quantity", ">", 0), ("location_id", "=", self.id)]
        )
        remaining = sum(quants.mapped("quantity"))
        move_line_qty_field = "qty_done"
        if move_lines:
            move_lines = move_lines.filtered(
                lambda m: m.state not in ("cancel", "done")
            )
            move_line_qty_field = "product_uom_qty"
        else:
            move_lines = self.env["stock.move.line"].search(
                [
                    ("state", "not in", ("cancel", "done")),
                    ("location_id", "=", self.id),
                    ("qty_done", ">", 0),
                ]
            )
        planned = remaining - sum(move_lines.mapped(move_line_qty_field))
        compare = float_compare(planned, 0, precision_rounding=0.01)
        return compare <= 0

    def should_bypass_reservation(self):
        self.ensure_one()
        if self.env.context.get("force_reservation"):
            return False
        return super().should_bypass_reservation()
