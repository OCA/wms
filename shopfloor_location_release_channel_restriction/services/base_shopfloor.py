# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import AbstractComponent


class BaseShopfloorProcess(AbstractComponent):
    _inherit = "base.shopfloor.process"

    def is_dest_location_valid(self, moves, location) -> bool:
        """
        Check if the scanned location has release channel restriction
        """
        res = super().is_dest_location_valid(moves, location)

        if any(
            not move._valid_location_release_channel_restriction(location)
            for move in moves.move_line_ids
        ):
            return False
        return res
