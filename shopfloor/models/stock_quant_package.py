from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    move_line_ids = fields.One2many(
        comodel_name="stock.move.line",
        inverse_name="package_id",
        readonly=True,
        help="Technical field. Move lines moving this package.",
    )

    planned_move_line_ids = fields.One2many(
        comodel_name="stock.move.line",
        inverse_name="result_package_id",
        readonly=True,
        help="Technical field. Move lines for which destination is this package.",
    )

    # TODO: we should refactor this like

    # source_planned_move_line_ids
    # destination_planned_move_line_ids

    # filter out done/cancel lines
