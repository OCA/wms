# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class BaseShopfloorProcess(AbstractComponent):
    _inherit = "base.shopfloor.process"

    def is_dest_location_valid(self, moves, location, pick_type=False):
        """
        Check if destination location is restricted for
        current moves
        """
        result = super().is_dest_location_valid(moves, location, pick_type=pick_type)
        for move in moves:
            if location._check_has_location_product_restriction(move.product_id):
                return bool(False and result)

        return result
