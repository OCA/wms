# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.addons.component.core import Component


class ShopfloorSingleProductTransfer(Component):
    _inherit = "shopfloor.single.product.transfer"

    def _set_quantity__check_location(self, move_line, location, confirmation=False):
        # We add an additional check to verify if the location requires packages
        # and return a message to the user accordingly.
        if (
            location.package_restriction != "norestriction"
            and not move_line.result_package_id
        ):
            message = self.msg_store.location_requires_package()
            return self._response_for_set_quantity(
                move_line, message=message, asking_confirmation=False
            )
        return super()._set_quantity__check_location(move_line, location, confirmation)
