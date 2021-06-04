# Copyright 2019-2021 Camptocamp SA
# Copyright 2019-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
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

    def _get_sorted_leaf_locations_orderby(self, products):
        if not self.pack_putaway_strategy == "abc":
            return super()._get_sorted_leaf_locations_orderby(products)
        product_abc = first(products).abc_storage or "a"
        if product_abc == "a":
            abc_seq = "a", "b", "c"
        elif product_abc == "b":
            abc_seq = "b", "c", "a"
        elif product_abc == "c":
            abc_seq = "c", "b", "a"
        self.env["stock.location"].flush(
            ["abc_storage", "max_height", "pack_putaway_sequence", "name"]
        )
        orderby = [
            "CASE WHEN max_height > 0 THEN max_height ELSE 'Infinity' END",
            "array_position(%s, abc_storage::text)",
            "pack_putaway_sequence",
            "random()",
        ]
        return ", ".join(orderby), [list(abc_seq)]
