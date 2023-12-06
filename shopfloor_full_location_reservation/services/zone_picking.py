# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ZonePicking(Component):
    _inherit = "shopfloor.zone.picking"

    def _handle_full_location_package_reservation(self, package):
        return package and self.work.menu.full_location_reservation

    def _handle_complete_mix_pack(self, package):
        """Return true if full location reservation is enabled
        otherwise if there is not more than one product on the package
        it will return False
        """
        if self._handle_full_location_package_reservation(package):
            return True
        return super()._handle_complete_mix_pack(package)

    def _set_destination_location(
        self, move_line, package, quantity, confirmation, location, barcode
    ):
        if self._handle_full_location_package_reservation(package):
            move_line._full_location_reservation(package_only=True)
            # Ensure all move lines have the same destination package.
            # If moves lines are in different pickings, the destination package
            # is not set in standard
            # a stock.package_level is only created if all products of the package
            # are contained in the picking
            move_line.search(
                [
                    ("package_id", "=", package.id),
                    ("state", "in", ("partially_available", "assigned")),
                    ("result_package_id", "!=", package.id),
                ]
            ).result_package_id = package
        return super()._set_destination_location(
            self, move_line, package, quantity, confirmation, location, barcode
        )
