# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class ShopfloorLocationContentTransfer(Component):
    _inherit = "shopfloor.location.content.transfer"

    def _set_dest_validate_location(self, move_ids, location, package, empty_package):
        message = super()._set_dest_validate_location(
            move_ids, location, package, empty_package
        )
        if not message:
            if location and location.package_restriction and not empty_package:
                message = self.msg_store.location_requires_package()
        return message
