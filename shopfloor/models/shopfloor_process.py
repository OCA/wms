from odoo import fields, models


class ShopfloorProcess(models.Model):
    _name = "shopfloor.process"
    _description = "a process to be run from the scanners"

    name = fields.Char(required=True)
    code = fields.Selection(selection="_selection_code", required=True)
    picking_type_ids = fields.One2many(
        "stock.picking.type", "process_id", string="Operation types"
    )
    menu_ids = fields.One2many(comodel_name="shopfloor.menu", inverse_name="process_id")

    def _selection_code(self):
        return [
            # these must match a REST service
            ("single_pack_putaway", "Single Pack Put-away"),
            ("single_pack_transfer", "Single Pack Transfer"),
        ]
