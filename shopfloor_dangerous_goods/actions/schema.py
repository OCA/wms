# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):

    _inherit = "shopfloor.schema.action"

    def move_line(self, with_packaging=False, with_picking=False):
        res = super().move_line(
            with_packaging=with_packaging, with_picking=with_picking
        )
        res["has_lq_products"] = {
            "type": "boolean",
            "nullable": False,
            "required": False,
        }
        return res

    def package(self, with_packaging=False):
        res = super().package(with_packaging=with_packaging)
        res["has_lq_products"] = {
            "type": "boolean",
            "nullable": False,
            "required": False,
        }
        return res
