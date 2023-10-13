# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.exceptions import ValidationError

from odoo.addons.component.core import AbstractComponent


class BaseShopfloorProcess(AbstractComponent):

    _inherit = "base.shopfloor.process"

    def validate_dest_location(self, moves, location):
        message = super().validate_dest_location(moves, location)
        if message:
            return message
        if location.package_restriction:
            try:
                moves._check_location_package_restriction(only_qty_done=False)
            except ValidationError as ex:
                return {
                    "message_type": "error",
                    "body": ex.name,
                }
