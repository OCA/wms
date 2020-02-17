from odoo import fields, models


class ShopfloorProcess(models.Model):
    _name = "shopfloor.process"
    _description = "a process to be run from the scanners"

    name = fields.Char(required=True)
    code = fields.Selection(selection="_selection_code", required=True)
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type", string="Operation Type"
    )
    menu_ids = fields.One2many(comodel_name="shopfloor.menu", inverse_name="process_id")

    def _selection_code(self):
        return [
            # these must match a REST service's '_usage'
            ("single_pack_putaway", "Single Pack Put-away"),
            ("single_pack_transfer", "Single Pack Transfer"),
            ("cluster_picking", "Cluster Picking"),
        ]
