# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopfloor.tests.test_actions_data_base import ActionsDataCaseBase


class TestShopfloorProductPackageType(ActionsDataCaseBase):
    def test_data_product_package_type(self):
        package_type = (
            self.env["stock.package.type"].sudo().create({"name": "Package Type A"})
        )
        self.product_a.package_type_id = package_type.id

        data = self.data.product(self.product_a)

        expected = {
            "package_type": {
                "id": package_type.id,
                "name": package_type.name,
                "display_name": package_type.display_name,
            },
        }
        self.assertDictContainsSubset(expected, data)
