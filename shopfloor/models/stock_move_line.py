from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    shopfloor_unloaded = fields.Boolean(default=False)
    shopfloor_postponed = fields.Boolean(
        default=False,
        copy=False,
        help="Technical field. "
        "Indicates if a the move has been postponed in a process.",
    )
