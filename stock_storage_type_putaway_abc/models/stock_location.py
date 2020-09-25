# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from random import shuffle

from odoo import api, fields, models
from odoo.fields import first

ABC_SELECTION = [("a", "A"), ("b", "B"), ("c", "C")]


class StockLocation(models.Model):

    _inherit = "stock.location"

    pack_putaway_strategy = fields.Selection(selection_add=[("abc", "Chaotic ABC")])
    display_abc_storage = fields.Boolean(compute="_compute_display_abc_storage")
    abc_storage = fields.Selection(ABC_SELECTION, required=True, default="b")

    @api.depends(
        "location_id",
        "location_id.pack_putaway_strategy",
        "location_id.display_abc_storage",
    )
    def _compute_display_abc_storage(self):
        for location in self:
            current_location = location.location_id
            display_abc_storage = current_location.display_abc_storage
            while current_location and not display_abc_storage:
                if current_location.pack_putaway_strategy == "abc":
                    display_abc_storage = True
                    break
                else:
                    current_location = current_location.location_id
            location.display_abc_storage = display_abc_storage

    def get_storage_locations(self, products=None):
        if products is None:
            products = self.env["product.product"]
        if self.pack_putaway_strategy == "abc":
            return self._get_abc_locations(products)
        return super().get_storage_locations(products)

    def _get_abc_locations(self, products):
        return self.leaf_location_ids._sort_abc_locations(first(products).abc_storage)

    def _sort_abc_locations(self, product_abc):
        product_abc = product_abc or "a"
        a_location_ids = []
        b_location_ids = []
        c_location_ids = []
        for loc in self:
            if loc.abc_storage == "a":
                a_location_ids.append(loc.id)
            elif loc.abc_storage == "b":
                b_location_ids.append(loc.id)
            elif loc.abc_storage == "c":
                c_location_ids.append(loc.id)
        shuffle(a_location_ids)
        shuffle(b_location_ids)
        shuffle(c_location_ids)
        if product_abc == "a":
            location_ids = a_location_ids + b_location_ids + c_location_ids
        elif product_abc == "b":
            location_ids = b_location_ids + c_location_ids + a_location_ids
        elif product_abc == "c":
            location_ids = c_location_ids + b_location_ids + a_location_ids
        else:
            raise ValueError("product_abc = %s" % product_abc)
        return self.env["stock.location"].browse(location_ids)
