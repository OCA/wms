# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _

from odoo.addons.component.core import AbstractComponent


class BaseShopfloorProcess(AbstractComponent):
    _inherit = "base.shopfloor.process"

    def is_dest_location_valid(self, moves, location):
        """
        Check if destination location is restricted for
        current moves
        """
        result = super().is_dest_location_valid(moves, location)
        for move in moves:
            if location._check_has_location_product_restriction(move.product_id):
                self.msg_store.add_message(
                    _(
                        "The location %(location_name)s contains already another "
                        "product than %(product_name)s",
                        location_name=location.name,
                        product_name=moves.mapped("product_id.display_name"),
                    )
                )
                return bool(False and result)

        return result
