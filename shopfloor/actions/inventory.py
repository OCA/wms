# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
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

    @property
    def inventory_model(self):
        # the _sf_inventory key bypass groups checks,
        # see comment in models/stock_inventory.py
        return self.env["stock.quant"].with_context(_sf_inventory=True)

    def create_draft_check_empty(self, location, product, ref=None):
        """Create a draft inventory for a product with a zero quantity"""
        return self._create_draft_inventory(location, product)

    def _inventory_exists(self, location, product, package=None, lot=None):
        """Return if an inventory for location and product exist"""
        domain = [
            ("location_id", "=", location.id),
            ("product_id", "=", product.id),
            ("inventory_quantity_set", "=", True),
        ]
        if package is not None:
            domain.append(("package_id", "=", package.id))
        if lot is not None:
            domain.append(("lot_id", "=", lot.id))
        return self.inventory_model.search_count(domain)

    def _create_draft_inventory(self, location, product):
        return self.inventory_model.sudo().create(
            {"location_id": location.id, "product_id": product.id}
        )

    def create_control_stock(self, location, product, package, lot, name=None):
        """Create a draft inventory so a user has to check a location

        If a draft or in progress inventory already exists for the same
        combination of product/package/lot, no inventory is created.
        """
        if not self._inventory_exists(location, product):
            self._create_draft_inventory(location, product)

    def create_stock_issue(self, move, location, package, lot):
        """Create an inventory for a stock issue

        It reduces the quantity in a location in a way that:
        * assigned move lines in other batch transfers stay assigned.
        * assigned move lines in same batch but already picked stay assigned.
        """
        other_lines = self._stock_issue_get_related_move_lines(
            move, location, package, lot
        )
        qty_to_keep = sum(other_lines.mapped("reserved_qty"))
        self.create_stock_correction(move, location, package, lot, qty_to_keep)
        move._action_assign()

    def create_stock_correction(self, move, location, package, lot, quantity):
        """Create an inventory with a forced quantity"""
        values = self._stock_correction_inventory_values(
            move, location, package, lot, quantity
        )
        inventory = self.inventory_model.sudo().create(values)
        inventory.action_apply_inventory()

    def _stock_issue_get_related_move_lines(self, move, location, package, lot):
        """Lookup for all the other moves lines that match given move line"""
        domain = [
            ("location_id", "=", location.id),
            ("product_id", "=", move.product_id.id),
            ("package_id", "=", package.id),
            ("lot_id", "=", lot.id),
            ("state", "in", ("assigned", "partially_available")),
        ]
        return self.env["stock.move.line"].search(domain)

    def _stock_correction_inventory_values(
        self, move, location, package, lot, line_qty
    ):
        return {
            "location_id": location.id,
            "product_id": move.product_id.id,
            "package_id": package.id,
            "lot_id": lot.id,
            "inventory_quantity": line_qty,
        }

    def _stock_issue_product_description(self, product, package, lot):
        parts = []
        if package:
            parts.append(package.name)
        parts.append(product.name)
        if lot.name:
            parts.append(_("Lot: ") + lot.name)
        return " - ".join(parts)
