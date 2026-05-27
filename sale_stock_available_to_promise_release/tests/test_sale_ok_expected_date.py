# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from .common import Common


class TestSaleOkExpectedDate(Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_2 = cls.env["product.product"].create(
            {
                "name": "Test Storable Product Two",
                "uom_id": cls.uom_unit.id,
                "type": "product",
            }
        )
        # Have a line on the order that will not activate the feature
        cls.line_2 = cls.env["sale.order.line"].create(
            {
                "order_id": cls.sale.id,
                "product_id": cls.product_2.id,
                "product_uom_qty": 100,
                "product_uom": cls.uom_unit.id,
            },
        )

    def test_expected_date_ok(self):
        self.sale.action_confirm()
        self._set_stock(self.product, 100)
        self.assertTrue(self.sale.is_ok_expected_delivery_date)

    def test_no_availability(self):
        self.sale.action_confirm()
        self.assertFalse(self.sale.is_ok_expected_delivery_date)

    def test_no_expected_date(self):
        self.sale.action_confirm()
        self.sale.expected_date = False
        self.assertFalse(self.sale.commitment_date)
        self.assertFalse(self.sale.is_ok_expected_delivery_date)

    def test_no_expected_date_for_service(self):
        self.line.unlink()
        self.product_2.type = "service"
        self.sale.action_confirm()
        self.assertFalse(self.sale.is_ok_expected_delivery_date)
