# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.shopfloor.tests.test_actions_data_base import ActionsDataCaseBase


class TestShopfloorVendorPackaging(ActionsDataCaseBase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.product = cls.move_a.move_line_ids.product_id
        vendor_packaging_type = (
            cls.env["product.packaging.type"]
            .sudo()
            .create(
                {
                    "name": "Test Vendor Packaging Type",
                    "code": "VP",
                    "sequence": 99,
                    "is_vendor_packaging": True,
                }
            )
        )
        vendor_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Test Vendor Packaging",
                    "qty": 15,
                    "packaging_type_id": vendor_packaging_type.id,
                }
            )
        )
        cls.product.sudo().update(
            {"packaging_ids": cls.product.packaging_ids | vendor_packaging}
        )

    def test_data_product(self):
        data = self.data.product(self.product, display_vendor_packaging=False)
        self.assert_schema(self.schema.product(), data)
        expected_packaging_codes = ["DEFAULT"]
        self.assertEqual(
            [packaging["code"] for packaging in data["packaging"]],
            expected_packaging_codes,
        )

    def test_data_product_with_vendor_packaging(self):
        data = self.data.product(self.product, display_vendor_packaging=True)
        self.assert_schema(self.schema.product(), data)
        expected_packaging_codes = ["DEFAULT", "VP"]
        self.assertEqual(
            [packaging["code"] for packaging in data["packaging"]],
            expected_packaging_codes,
        )
