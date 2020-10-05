# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from random import shuffle

from odoo import api, fields, models
from odoo.fields import first

ABC_SELECTION = [("a", "A"), ("b", "B"), ("c", "C")]


def gather_location_ids(abc_sorted, max_heights_sorted, locations_grouped):
    """Return a list of location IDs sorted on `abc_sorted` then
    on `max_heights_sorted`.
    """
    location_ids = []
    for abc_key in abc_sorted:
        group_ids_per_height = locations_grouped.get(abc_key)
        if not group_ids_per_height:
            continue
        for max_height in max_heights_sorted:
            location_ids.extend(group_ids_per_height.get(max_height, []))
    return location_ids


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
        # group locations by abc_storage and max_height
        data = self.read_group(
            [("id", "in", self.ids)], ["max_height"], ["max_height"],
        )
        locations_grouped = {}
        max_heights = set()
        for line in data:
            domain = line["__domain"]
            locations = self.search(domain)
            for loc in locations:
                locations_grouped.setdefault(loc.abc_storage, {}).setdefault(
                    line["max_height"], []
                )
                locations_grouped[loc.abc_storage][line["max_height"]].append(loc.id)
            # keep a list of available max heights
            max_heights.add(line["max_height"])
        # sort max heights and take care to put any 0 value at the end
        max_heights = list(max_heights)
        max_heights.sort()
        if 0 in max_heights:
            max_heights.pop(max_heights.index(0))
            max_heights.append(0)
        # shuffle each abc_storage/max_height chunk
        for line in locations_grouped.values():
            for max_height in line:
                shuffle(line[max_height])
        # prepare the result
        if product_abc == "a":
            location_ids = gather_location_ids("abc", max_heights, locations_grouped)
        elif product_abc == "b":
            location_ids = gather_location_ids("bca", max_heights, locations_grouped)
        elif product_abc == "c":
            location_ids = gather_location_ids("cba", max_heights, locations_grouped)
        else:
            raise ValueError("product_abc = %s" % product_abc)
        return self.env["stock.location"].browse(location_ids)
