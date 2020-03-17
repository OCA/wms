from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    # TODO use a serialized field
    shopfloor_unloaded = fields.Boolean(default=False)
    shopfloor_postponed = fields.Boolean(
        default=False,
        copy=False,
        help="Technical field. "
        "Indicates if a the move has been postponed in a process.",
    )
    shopfloor_checkout_packed = fields.Boolean(default=False)

    # we search lines based on their location in some workflows
    location_id = fields.Many2one(index=True)
