# Copyright 2021 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _on_order_route(self):
        res = super()._on_order_route()
        dropshipping_route = self.env.ref("stock_dropshipping.route_drop_shipping")
        product_is_dropshipping = dropshipping_route in self.product_id.route_ids
        line_is_dropshipping = dropshipping_route == self.route_id
        return res or product_is_dropshipping or line_is_dropshipping
