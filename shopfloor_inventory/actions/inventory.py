# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class InventoryAction(Component):
    _inherit = "shopfloor.inventory.action"

    @property
    def inventory_line_model(self):
        return self.env["stock.inventory.line"]

    def create_inventory_line(self, inventory_id, location_id, product_id, product_qty):
        return self.inventory_line_model.sudo().create(
            {
                "inventory_id": inventory_id,
                "location_id": location_id,
                "product_id": product_id,
                "product_qty": product_qty,
            }
        )
