# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def action_open_delivery_wizard(self):
        res = super().action_open_delivery_wizard()
        wh_carrier = self.warehouse_id.delivery_carrier_id
        if (
            not self.env.context.get("carrier_recompute")
            and not res["context"].get("default_carrier_id")
            and wh_carrier
        ):
            res["context"]["default_carrier_id"] = wh_carrier.id
        return res
