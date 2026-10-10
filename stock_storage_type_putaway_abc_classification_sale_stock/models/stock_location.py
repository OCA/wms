# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockLocation(models.Model):

    _inherit = "stock.location"

    def _get_sorted_leaf_locations_orderby_abc(self, products):
        """
        'self' is the location we want to put products and apply the
        putaway strategy.
        Evaluate the abc classification profile ids in order to retrieve
        the corresponding one.
        """
        location_level = products.abc_classification_product_level_ids.filtered(
            lambda level, location=self: level.profile_type == "sale_stock"
            and level.profile_id.warehouse_id == location.warehouse_id
        )

        if not location_level:
            return super()._get_sorted_leaf_locations_orderby_abc(products)
        return location_level.level_id.name
