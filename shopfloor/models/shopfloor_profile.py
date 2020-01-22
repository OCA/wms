from odoo import api, fields, models


class ShopfloorProfile(models.Model):
    _name = "shopfloor.profile"
    _description = "Shopfloor profile settings"

    name = fields.Char(required=True)
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        required=True,
        default=lambda self: self._default_warehouse_id(),
    )
    operation_group_ids = fields.Many2many(
        "shopfloor.operation.group",
        string="Shopfloor Operation Groups",
        help="When unset, all users can use the profile. When set,"
        "only users belonging to at least one group can use the profile.",
    )
    user_id = fields.Many2one(
        "res.users",
        copy=False,
        help="Optional user using the profile. When a profile has a"
        "user assigned to it, the user is not allowed to use another profile.",
    )

    _sql_constraints = [
        (
            "user_id_uniq",
            "unique(user_id)",
            "A user can be assigned to only one profile.",
        )
    ]

    @api.model
    def _default_warehouse_id(self):
        wh = self.env["stock.warehouse"].search([])
        if len(wh) == 1:
            return wh
