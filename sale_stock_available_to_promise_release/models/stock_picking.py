# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_date_expected = fields.Date(
        string="Delivery Date", related="group_id.date_expected", store=True
    )

    def _get_shipping_policy(self):
        # Override the method to get the shipping policy from the related order:
        # We want to release the transfers based on the shipping policy of the
        # order, and the policy defined at the transfer level will be used only
        # to process the transfer as usual.
        self.ensure_one()
        return self.sale_id.picking_policy or super()._get_shipping_policy()
