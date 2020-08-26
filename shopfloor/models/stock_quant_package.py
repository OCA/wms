from odoo import _, api, exceptions, fields, models


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
    # TODO: review other fields
    reserved_move_line_ids = fields.One2many(
        comodel_name="stock.move.line", compute="_compute_reserved_move_lines",
    )

    def _get_reserved_move_lines(self):
        return self.env["stock.move.line"].search(
            [("package_id", "=", self.id), ("state", "not in", ("done", "cancel"))]
        )

    @api.depends("move_line_ids.state")
    def _compute_reserved_move_lines(self):
        for rec in self:
            rec.update({"reserved_move_line_ids": rec._get_reserved_move_lines()})

    # TODO: we should refactor this like

    # source_planned_move_line_ids
    # destination_planned_move_line_ids

    # filter out done/cancel lines

    @api.constrains("name")
    def _constrain_name_unique(self):
        for rec in self:
            if self.search_count([("name", "=", rec.name), ("id", "!=", rec.id)]):
                raise exceptions.UserError(_("Package name must be unique!"))
