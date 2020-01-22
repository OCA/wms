from odoo import fields, models


class ShopfloorMenu(models.Model):
    _name = "shopfloor.menu"
    _description = "Menu displayed in the scanner application"
    _order = "sequence"

    name = fields.Char(translate=True)
    sequence = fields.Integer()
    operation_group_ids = fields.Many2many(
        "shopfloor.operation.group", string="Groups", help="visible for these groups"
    )
    process_id = fields.Many2one("shopfloor.process", name="Process", required=True)
    process_code = fields.Selection(related="process_id.code", readonly=True)
