# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class InventoryAction(Component):

    _inherit = "shopfloor.inventory.action"

    def _create_stock_issue_loss_quantity(self, move, location, package, lot, lines):
        if lines:
            lines._lose_quantity()
            return
        # No live move line to act on (the move itself was canceled
        # outright, e.g. an ad-hoc one created by the operator): lock
        # whatever quant is still there directly, product/location/lot/
        # package, the same way `_lose_quantity` would have done
        # internally had there been a move line to call it on.
        quants = self.env["stock.quant"]._gather(
            product_id=move.product_id,
            location_id=location,
            lot_id=lot,
            package_id=package,
            strict=True,
        )
        loss_type = location.warehouse_id.loss_type_id
        for quant in quants:
            quant._lock_with_picking_type(loss_type)
