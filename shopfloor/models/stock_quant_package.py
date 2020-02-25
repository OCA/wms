from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    dest_move_line_ids = fields.One2many(
        comodel_name="stock.move.line",
        inverse_name="result_package_id",
        readonly=True,
        help="Technical field. Move lines for which destination" " is this package.",
    )
