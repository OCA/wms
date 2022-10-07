# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields

from odoo.addons.shopfloor.tests.test_actions_data import ActionsDataCase

from .test_actions_data_base import InventoryActionsDataCaseBase


class InventoryActionsDataCase(ActionsDataCase, InventoryActionsDataCaseBase):
    def test_data_inventory(self):
        self.inventory.action_start()
        data = self.data.inventory(self.inventory)
        expected = self._expected_inventory(self.inventory)
        self.assertEqual(
            data.pop("date").replace("T", " "),
            fields.Datetime.to_string(self.inventory.date),
        )
        self.assertDictEqual(data, expected)

    def test_data_inventory_with_location(self):
        self.inventory.action_start()
        data = self.data.inventory(self.inventory, with_locations=True)
        expected = self._expected_inventory(self.inventory)
        expected.update(
            {
                "locations": self.data.inventory_locations(
                    self.inventory.sub_location_ids
                ),
            }
        )
        data.pop("date")
        self.assertDictEqual(data, expected)

    def test_data_inventory_line(self):
        location = self.stock_location
        product = (
            self.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Test",
                    "type": "product",
                    "barcode": "test_inventory",
                    "default_code": "test_inventory",
                }
            )
        )
        qty = 1.0
        package = self.env["stock.quant.package"].create(
            {"packaging_id": self.packaging.id}
        )
        lot = self.env["stock.production.lot"].create(
            {
                "product_id": product.id,
                "company_id": self.env.company.id,
            }
        )
        self.env["stock.quant"]._update_available_quantity(
            product, location, qty, lot_id=lot, package_id=package
        )
        self.inventory.action_start()
        line = self.inventory.line_ids.filtered(
            lambda l: l.product_id == product and l.location_id == location
        )
        data = self.data.inventory_line(line)
        expected = {
            "id": line.id,
            "product_qty": 0.0,
            "theoretical_qty": qty,
            "product": self._expected_product(product),
            "lot": {
                "id": lot.id,
                "name": lot.name,
                "ref": None,
            },
            "package": self._expected_package(package),
            "location": self._expected_location(location),
        }
        self.assertDictEqual(data, expected)
