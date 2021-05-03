# Copyright 2021 <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    pre_location_ids = fields.Many2many(
        comodel_name="stock.location",
        relation="stock_pre_location",
        column1="pre_location_id",
        column2="dest_location_id",
        string="Pre Location",
        help="Locations where incoming goods will be pre-sorted",
        # TODO: add a domain to restict locations
    )

    @property
    def _putaway_strategies(self):
        strategies = super()._putaway_strategies
        return strategies + ["mirror"]

    def _get_putaway_strategy(self, product):

        # Dest location like WH/STOCK
        dest_location_ids = self.env.context.get("_pre_location_dest")

        if not dest_location_ids:
            return super()._get_putaway_strategy(product)

        dest_location_id = dest_location_ids[:1]  # TODO make it multi dest
        dest_putaway_location = dest_location_id.with_context(
            _pre_location_dest=False
        )._get_putaway_strategy(product)

        if not dest_putaway_location:
            return super()._get_putaway_strategy(product)

        pre_location = dest_putaway_location._get_pre_location(self)
        if not pre_location:
            return super()._get_putaway_strategy(product)
        else:
            return pre_location

    def _get_pre_location(self, target_loc):
        """For a given location return the first
        pre_location found in location tree from child
        to parent location (recursively)
        If none found, returns False"""

        childs_ids_of_target = target_loc.children_ids

        for pre_location in self.pre_location_ids:
            if pre_location.id in childs_ids_of_target.ids:
                # got it !
                return pre_location
        if not self.location_id:
            return False
        return self.location_id._get_pre_location(target_loc)
