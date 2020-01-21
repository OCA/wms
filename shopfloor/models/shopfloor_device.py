from odoo import fields, models


class ShopfloorDevice(models.Model):
    _name = "shopfloor.device"
    _description = "Shopfloor device settings"

    name = fields.Char(required=True)
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        required=True,
    )
    shopfloor_operation_group_ids = fields.Many2many(
        "shopfloor.operation.group",
        string="Shopfloor Operation Groups"
    )
    user_id = fields.Many2one(
        "res.users",
        help="Optional user using the device. The device will"
        "use this configuration when the users logs in the client "
        "application."
    )
    shopfloor_current_process = fields.Char(readonly=True)
    shopfloor_last_call = fields.Char(readonly=True)
    shopfloor_picking_id = fields.Many2one('stock.picking', readonly=True)
