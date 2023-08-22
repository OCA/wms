# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component


class ShopfloorZonePicking(Component):
    _inherit = "shopfloor.zone.picking"

    def _validate_destination(self, location, moves):
        message = super()._validate_destination(location, moves)
        if message:
            return message
        if location.package_restriction != "norestriction":
            try:
                moves._check_location_package_restriction(only_qty_done=False)
            except ValidationError as ex:
                # __import__("pdb").set_trace()
                return {
                    "message_type": "error",
                    "body": ex.name,
                }
                # return self.msg_store.location_has_restrictions()
