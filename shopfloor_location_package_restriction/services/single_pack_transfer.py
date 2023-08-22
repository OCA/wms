# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component


class ShopfloorSinglePackTransfer(Component):
    _inherit = "shopfloor.single.pack.transfer"

    def _validate_destination_location(self, package_level, location):
        response = super()._validate_destination_location(package_level, location)
        if response:
            return response
        if location.package_restriction != "norestriction":
            # Not sure about this
            # Could there be more move lines being checked than intended ?
            moves = package_level.move_line_ids.move_id
            try:
                moves._check_location_package_restriction(location)
            except ValidationError:
                return self._response_for_scan_location(
                    package_level, message=self.msg_store.location_has_restrictions()
                )
