from odoo import api, fields, models


class ShopfloorDevice(models.Model):
    _name = "shopfloor.device"
    _description = "Shopfloor device settings"

    name = fields.Char(required=True)
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        required=True,
        default=lambda self: self._default_warehouse_id(),
    )
    operation_group_ids = fields.Many2many(
        "shopfloor.operation.group",
        string="Shopfloor Operation Groups",
        help="When unset, all users can use the device. When set,"
        "only users belonging to at least one group can use the device.",
    )
    user_id = fields.Many2one(
        "res.users",
        copy=False,
        help="Optional user using the device. The device will"
        "use this configuration when the users logs in the client "
        "application.",
    )
    shopfloor_current_process = fields.Char(readonly=True)
    shopfloor_last_call = fields.Char(readonly=True)
    shopfloor_picking_id = fields.Many2one("stock.picking", readonly=True)

    _sql_constraints = [
        (
            "user_id_uniq",
            "unique(user_id)",
            "A user can be assigned to only one device.",
        )
    ]

    @api.model
    def _default_warehouse_id(self):
        wh = self.env["stock.warehouse"].search([])
        if len(wh) == 1:
            return wh
