from odoo import _

from odoo.addons.component.core import Component


class InventoryAction(Component):
    """Provide methods to work with inventories

    Several processes have to create inventories at some point,
    for instance when there is a stock issue.
    """

    _name = "shopfloor.inventory.action"
    _inherit = "shopfloor.process.action"
    _usage = "inventory"

    def create_draft_check_empty(self, location, product, ref=None):
        """Create a draft inventory for a product with a zero quantity"""
        if ref:
            name = _("Zero check issue on location {} ({})").format(location.name, ref)
        else:
            name = _("Zero check issue on location {}").format(location.name)
        inventory = self.env["stock.inventory"].create(
            {
                "name": name,
                "location_ids": [(6, 0, location.ids)],
                "product_ids": [(6, 0, product.ids)],
            }
        )
        return inventory
