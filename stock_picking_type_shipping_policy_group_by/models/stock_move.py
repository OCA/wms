# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _domain_search_picking_handle_move_type(self):
        """Hook overloaded to build the move_type criteria based on the
        shipping policy of the picking type.
        """
        shipping_policy = self.picking_type_id.shipping_policy
        move_types_mapping = {
            "force_as_soon_as_possible": "direct",
            "force_all_products_ready": "one",
            "procurement_group": self.group_id.move_type,
        }
        return [("move_type", "=", move_types_mapping[shipping_policy])]
