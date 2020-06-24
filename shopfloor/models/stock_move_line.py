from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    # TODO use a serialized field
    shopfloor_unloaded = fields.Boolean(default=False)
    shopfloor_postponed = fields.Boolean(
        default=False,
        copy=False,
        help="Technical field. "
        "Indicates if a the move has been postponed in a barcode scenario.",
    )
    shopfloor_checkout_done = fields.Boolean(default=False)
    shopfloor_user_id = fields.Many2one(comodel_name="res.users", index=True)

    # we search lines based on their location in some workflows
    location_id = fields.Many2one(index=True)
    package_id = fields.Many2one(index=True)

    # allow domain on picking_id.xxx without too much perf penalty
    picking_id = fields.Many2one(auto_join=True)
