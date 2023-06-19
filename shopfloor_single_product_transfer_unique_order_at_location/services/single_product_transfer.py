# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class ShopfloorSingleProductTransfer(Component):
    _inherit = "shopfloor.single.product.transfer"

    def _set_quantity__check_location(
        self, move_line, location=False, confirmation=False
    ):
        res = super()._set_quantity__check_location(move_line, location, confirmation)
        # Could also be asking for confirmation with a warning
        if res and res.get("message", {}).get("message_type", "") == "error":
            return res
        try:
            move_line._check_same_order_at_destination(location)
        except UserError:
            message = self.msg_store.dest_location_not_allowed()
            return self._response_for_set_quantity(move_line, message=message)
        return res
