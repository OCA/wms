# Copyright 2021 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo.addons.sale_stock_available_to_promise_release.tests.common import Common


class TestDropshipping(Common):
    @classmethod
    def setUpClassProduct(cls):
        super().setUpClassProduct()
        supplier = cls.env.ref("base.res_partner_1")
        cls.dropshipping_route = cls.env.ref("stock_dropshipping.route_drop_shipping")
        cls.product.route_ids = cls.dropshipping_route
        cls.product.seller_ids = cls.env["product.supplierinfo"].create(
            {
                "name": supplier.id,
                "product_id": cls.product.id,
            }
        )

    def test_available_dropshipping(self):
        self.sale.action_confirm()
        self.assertEqual(self.line.availability_status, "on_order")
